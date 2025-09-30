from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from ..database import get_db
from ..repositories.full_time_job_repository import FullTimeJobRepository
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..repositories.team_member_repository import TeamMemberRepository
from ..schemas.full_time_job import (
    FullTimeJobCreate,
    FullTimeJobUpdate,
    FullTimeJobResponse,
    FullTimeJobListResponse,
    UserFullTimeJobsResponse
)
from ..schemas.common import MessageResponse, SuccessResponse
from ..utils.auth import get_current_user
from ..utils.permissions import has_permission, Permission
from ..models.team_member import TeamMemberRole, TeamMemberStatus
from ..models.user import User

router = APIRouter(prefix="/full-time-jobs", tags=["Full Time Job"])


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Get current user if authorization header is provided, otherwise return None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        # Import here to avoid circular imports
        from ..utils.auth import verify_token
        from ..repositories.user_repository import UserRepository
        from ..database import get_db
        
        # Get database session
        db = next(get_db())
        user_repo = UserRepository(db)
        
        # Verify token and get user
        payload = verify_token(token)
        if payload and 'sub' in payload:
            user_id = int(payload['sub'])
            user = user_repo.get_by_id(user_id)
            return user
        return None
    except Exception:
        return None


def check_job_access_permission(
    user_id: int, 
    job_id: int, 
    required_permission: Permission, 
    db: Session
) -> Tuple[bool, dict, str]:
    """
    Check if user has permission to access a specific job
    Returns: (has_permission, job_data, error_message)
    """
    job_repo = FullTimeJobRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    team_repo = TeamMemberRepository(db)
    
    # Get job details
    job = job_repo.get_by_id(job_id, user_id)
    if not job:
        return False, {}, "Full-time job not found"
    
    corporate_profile_id = job['company_id']
    
    # Check if corporate profile exists and is active
    profile = corporate_repo.get_by_id(corporate_profile_id)
    if not profile:
        return False, job, "Corporate profile not found"
    
    if not profile.is_active:
        return False, job, "Corporate profile is not active"
    
    # Check if user is owner
    if profile.user_id == user_id:
        return True, job, ""
    
    # Check if user is team member with required permission
    team_member = team_repo.get_by_user_and_corporate_profile(user_id, corporate_profile_id)
    if not team_member or team_member.status != TeamMemberStatus.ACCEPTED:
        return False, job, "You don't have access to this job"
    
    # Check permission
    if not has_permission(user_id, corporate_profile_id, required_permission, db):
        return False, job, f"You don't have permission to {required_permission.value.replace('_', ' ')} this job"
    
    return True, job, ""


def get_user_corporate_profiles(user_id: int, db: Session) -> List[int]:
    """Get all corporate profile IDs where user has access (owner or team member)"""
    corporate_repo = CorporateProfileRepository(db)
    team_repo = TeamMemberRepository(db)
    
    # Get owned profiles
    owned_profile = corporate_repo.get_by_user_id(user_id)
    corporate_profile_ids = []
    if owned_profile:
        corporate_profile_ids.append(owned_profile.id)
    
    # Get team member profiles
    team_memberships = team_repo.get_user_team_memberships_accepted(user_id)
    corporate_profile_ids.extend([membership.corporate_profile_id for membership in team_memberships])
    
    return list(set(corporate_profile_ids))  # Remove duplicates


@router.post("/", response_model=SuccessResponse, tags=["Full Time Job"])
async def create_full_time_job(
    full_time_job: FullTimeJobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new full-time job for a specific corporate profile"""
    try:
        corporate_repo = CorporateProfileRepository(db)
        job_repo = FullTimeJobRepository(db)
        team_repo = TeamMemberRepository(db)
        
        # Get corporate_profile_id from request body
        corporate_profile_id = full_time_job.corporate_profile_id
        
        # 1. Check if corporate profile exists and is active
        profile = corporate_repo.get_by_id(corporate_profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Corporate profile not found"
            )
        
        if not profile.is_active or not profile.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corporate profile must be verified and active to create jobs"
            )
        
        # 2. Check user permissions for this corporate profile
        user_role = None
        can_create_jobs = False
        
        # Check if user is the owner
        if profile.user_id == current_user.id:
            user_role = TeamMemberRole.OWNER
            can_create_jobs = True
        else:
            # Check if user is a team member with create_job permission
            team_member = team_repo.get_by_user_and_corporate_profile(current_user.id, corporate_profile_id)
            if team_member and team_member.status == TeamMemberStatus.ACCEPTED:
                user_role = team_member.role
                # Check if role has create_job permission
                can_create_jobs = has_permission(current_user.id, corporate_profile_id, Permission.CREATE_JOB, db)
        
        if not can_create_jobs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create jobs for this company"
            )
        
        # 3. Create the job with context
        db_job = job_repo.create_with_context(
            full_time_job, 
            corporate_profile_id, 
            current_user.id, 
            user_role
        )
        
        # 4. Return success response with job data
        return SuccessResponse(
            status="success",
            msg="Full time job successfully created",
            data=db_job
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/", response_model=FullTimeJobListResponse, tags=["Full Time Job"])
async def get_all_full_time_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get all full-time jobs with pagination"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    jobs = job_repo.get_all_active(skip=skip, limit=size, current_user_id=current_user.id if current_user else None)
    total = job_repo.count_active()
    
    # Convert dict responses to FullTimeJobResponse objects
    response_jobs = []
    for job in jobs:
        response_data = FullTimeJobResponse(**job)
        response_jobs.append(response_data)
    
    return FullTimeJobListResponse(
        jobs=response_jobs,
        total=total,
        page=page,
        size=size
    )


@router.get("/search", response_model=FullTimeJobListResponse, tags=["Full Time Job"])
async def search_full_time_jobs(
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    skill_ids: Optional[str] = Query(None, description="Comma-separated list of skill IDs"),
    min_salary: Optional[float] = Query(None, ge=0),
    max_salary: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Search full-time jobs with filters including skill IDs"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    # Parse skill_ids from comma-separated string
    skill_id_list = None
    if skill_ids:
        try:
            skill_id_list = [int(id.strip()) for id in skill_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid skill_ids format. Use comma-separated integers."
            )
    
    jobs = job_repo.search_jobs(
        title=title,
        location=location,
        experience_level=experience_level,
        work_mode=work_mode,
        skill_ids=skill_id_list,
        min_salary=min_salary,
        max_salary=max_salary,
        skip=skip,
        limit=size,
        current_user_id=current_user.id if current_user else None
    )
    
    # Convert dict responses to FullTimeJobResponse objects
    response_jobs = []
    for job in jobs:
        response_data = FullTimeJobResponse(**job)
        response_jobs.append(response_data)
    
    return FullTimeJobListResponse(
        jobs=response_jobs,
        total=len(response_jobs),  # For search, we return actual results count
        page=page,
        size=size
    )


@router.get("/user/me", response_model=UserFullTimeJobsResponse, tags=["Full Time Job"])
async def get_my_full_time_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's full-time jobs (created by user + accessible from team memberships)"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    # Get all jobs user can access (from owned and team member corporate profiles)
    jobs = job_repo.get_user_accessible_jobs(current_user.id, skip=skip, limit=size)
    total = job_repo.count_user_accessible_jobs(current_user.id)
    
    # Convert dict responses to FullTimeJobResponse objects
    response_jobs = []
    for job in jobs:
        response_data = FullTimeJobResponse(**job)
        response_jobs.append(response_data)
    
    return UserFullTimeJobsResponse(
        user_jobs=response_jobs,
        total=total,
        page=page,
        size=size
    )


@router.get("/my-full-time-jobs", response_model=UserFullTimeJobsResponse, tags=["Full Time Job"])
async def get_my_full_time_jobs_with_filters(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    job_status: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_salary: Optional[float] = Query(None, ge=0, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, ge=0, description="Filter by maximum salary"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's accessible full-time jobs with advanced filtering (requires VIEW_JOB permission)"""
    try:
        job_repo = FullTimeJobRepository(db)
        skip = (page - 1) * size
        
        # Get user's accessible corporate profiles
        corporate_profile_ids = get_user_corporate_profiles(current_user.id, db)
        
        if not corporate_profile_ids:
            return UserFullTimeJobsResponse(
                user_jobs=[],
                total=0,
                page=page,
                size=size
            )
        
        # Get filtered jobs from accessible corporate profiles
        jobs = job_repo.get_by_corporate_profiles_with_filters(
            corporate_profile_ids=corporate_profile_ids,
            skip=skip,
            limit=size,
            status=job_status,
            job_type=job_type,
            experience_level=experience_level,
            work_mode=work_mode,
            location=location,
            min_salary=min_salary,
            max_salary=max_salary,
            current_user_id=current_user.id
        )
        
        total = job_repo.count_by_corporate_profiles_with_filters(
            corporate_profile_ids=corporate_profile_ids,
            status=job_status,
            job_type=job_type,
            experience_level=experience_level,
            work_mode=work_mode,
            location=location,
            min_salary=min_salary,
            max_salary=max_salary
        )
        
        # Convert dict responses to FullTimeJobResponse objects
        response_jobs = []
        for job in jobs:
            response_data = FullTimeJobResponse(**job)
            response_jobs.append(response_data)
        
        return UserFullTimeJobsResponse(
            user_jobs=response_jobs,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve filtered jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def get_full_time_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full-time job by ID (requires VIEW_JOB permission)"""
    try:
        # Check if user has permission to view this job
        has_access, job_data, error_msg = check_job_access_permission(
            current_user.id, job_id, Permission.VIEW_JOB, db
        )
        
        if not has_access:
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg
                )
        
        # Convert dict response to FullTimeJobResponse object
        response_data = FullTimeJobResponse(**job_data)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job: {str(e)}"
        )


@router.put("/{job_id}", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def update_full_time_job(
    job_id: int,
    full_time_job: FullTimeJobUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update full-time job (requires UPDATE_JOB permission)"""
    try:
        # Check if user has permission to update this job
        has_access, job_data, error_msg = check_job_access_permission(
            current_user.id, job_id, Permission.UPDATE_JOB, db
        )
        
        if not has_access:
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg
                )
        
        # Update the job
        job_repo = FullTimeJobRepository(db)
        updated_job = job_repo.update(job_id, full_time_job)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update job"
            )
        
        # Convert dict response to FullTimeJobResponse object
        response_data = FullTimeJobResponse(**updated_job)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )


@router.delete("/{job_id}", response_model=MessageResponse, tags=["Full Time Job"])
async def delete_full_time_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete full-time job (requires DELETE_JOB permission)"""
    try:
        # Check if user has permission to delete this job
        has_access, job_data, error_msg = check_job_access_permission(
            current_user.id, job_id, Permission.DELETE_JOB, db
        )
        
        if not has_access:
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg
                )
        
        # Delete the job
        job_repo = FullTimeJobRepository(db)
        success = job_repo.delete(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete job"
            )
        
        return MessageResponse(message="Full-time job deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


@router.patch("/{job_id}/status", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def change_job_status(
    job_id: int,
    new_status: str = Query(..., regex="^(ACTIVE|CLOSED|DRAFT)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change job status (requires UPDATE_JOB permission)"""
    try:
        # Check if user has permission to update this job
        has_access, job_data, error_msg = check_job_access_permission(
            current_user.id, job_id, Permission.UPDATE_JOB, db
        )
        
        if not has_access:
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg
                )
        
        # Change status
        job_repo = FullTimeJobRepository(db)
        updated_job = job_repo.change_status(job_id, new_status)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change job status"
            )
        
        # Convert dict response to FullTimeJobResponse object
        response_data = FullTimeJobResponse(**updated_job)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change job status: {str(e)}"
        )
