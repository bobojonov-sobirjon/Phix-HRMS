from fastapi import APIRouter, Depends, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from ..db.database import get_db
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
from ..utils.auth import get_current_user, get_current_user_optional
from ..utils.decorators import handle_errors
from ..utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    forbidden_error,
    validate_entity_exists
)
from ..utils.permissions import has_permission, Permission, is_admin_user, check_admin_or_owner
from ..models.team_member import TeamMemberRole, TeamMemberStatus

router = APIRouter(prefix="/full-time-jobs", tags=["Full Time Job"])


# Removed local get_current_user_optional - using the one from app.utils.auth instead


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
    
    job = job_repo.get_by_id(job_id, user_id)
    if not job:
        return False, {}, "Full-time job not found"
    
    corporate_profile_id = job['company_id']
    
    profile = corporate_repo.get_by_id(corporate_profile_id)
    if not profile:
        return False, job, "Corporate profile not found"
    
    if not profile.is_active:
        return False, job, "Corporate profile is not active"
    
    if profile.user_id == user_id:
        return True, job, ""
    
    team_member = team_repo.get_by_user_and_corporate_profile(user_id, corporate_profile_id)
    if not team_member or team_member.status != TeamMemberStatus.ACCEPTED:
        return False, job, "You don't have access to this job"
    
    if not has_permission(user_id, corporate_profile_id, required_permission, db):
        return False, job, f"You don't have permission to {required_permission.value.replace('_', ' ')} this job"
    
    return True, job, ""


def get_user_corporate_profiles(user_id: int, db: Session) -> List[int]:
    """Get all corporate profile IDs where user has access (owner or team member)"""
    corporate_repo = CorporateProfileRepository(db)
    team_repo = TeamMemberRepository(db)
    
    owned_profile = corporate_repo.get_by_user_id(user_id)
    corporate_profile_ids = []
    if owned_profile:
        corporate_profile_ids.append(owned_profile.id)
    
    team_memberships = team_repo.get_user_team_memberships_accepted(user_id)
    corporate_profile_ids.extend([membership.corporate_profile_id for membership in team_memberships])
    
    return list(set(corporate_profile_ids))


@router.post("/", response_model=SuccessResponse, tags=["Full Time Job"])
@handle_errors
async def create_full_time_job(
    full_time_job: FullTimeJobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new full-time job for a specific corporate profile"""
    corporate_repo = CorporateProfileRepository(db)
    job_repo = FullTimeJobRepository(db)
    team_repo = TeamMemberRepository(db)
    
    corporate_profile_id = full_time_job.corporate_profile_id
    
    profile = corporate_repo.get_by_id(corporate_profile_id)
    validate_entity_exists(profile, "Corporate profile")
    
    if not profile.is_active or not profile.is_verified:
        raise bad_request_error("Corporate profile must be verified and active to create jobs")
    
    user_role = None
    can_create_jobs = False
    
    if is_admin_user(current_user.email):
        can_create_jobs = True
        user_role = TeamMemberRole.OWNER
    elif profile.user_id == current_user.id:
        user_role = TeamMemberRole.OWNER
        can_create_jobs = True
    else:
        team_member = team_repo.get_by_user_and_corporate_profile(current_user.id, corporate_profile_id)
        if team_member and team_member.status == TeamMemberStatus.ACCEPTED:
            user_role = team_member.role
            can_create_jobs = has_permission(current_user.id, corporate_profile_id, Permission.CREATE_JOB, db)
    
    if not can_create_jobs:
        raise forbidden_error("You don't have permission to create jobs for this company")
    
    print(f"[DEBUG POST] Creating job with data: title={full_time_job.title}, status={full_time_job.status}, pay_period={full_time_job.pay_period}")
    formatted_job = job_repo.create_with_context(
        full_time_job, 
        corporate_profile_id, 
        current_user.id, 
        user_role
    )
    print(f"[DEBUG POST] Job created successfully with ID: {formatted_job.get('id')}, status={formatted_job.get('status')}")
    
    return success_response(
        data=formatted_job,
        message="Full time job successfully created"
    )


@router.get("/", response_model=FullTimeJobListResponse, tags=["Full Time Job"])
async def get_all_full_time_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    title: Optional[str] = Query(None, description="Filter by job title (partial match)"),
    location: Optional[str] = Query(None, description="Filter by location (partial match)"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode"),
    skill_ids: Optional[str] = Query(None, description="Comma-separated list of skill IDs"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    min_salary: Optional[float] = Query(None, ge=0, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, ge=0, description="Filter by maximum salary"),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get all full-time jobs with pagination and filters"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    skill_id_list = None
    if skill_ids:
        try:
            skill_id_list = [int(id.strip()) for id in skill_ids.split(',') if id.strip()]
        except ValueError:
            from ..utils.response_helpers import bad_request_error
            raise bad_request_error("Invalid skill_ids format. Use comma-separated integers.")
    
    jobs = job_repo.get_all_active(
        skip=skip, 
        limit=size, 
        current_user_id=current_user.id if current_user else None, 
        category_id=category_id, 
        subcategory_id=subcategory_id,
        title=title,
        location=location,
        experience_level=experience_level,
        work_mode=work_mode,
        skill_ids=skill_id_list,
        min_salary=min_salary,
        max_salary=max_salary
    )
    
    total = job_repo.count_active(
        category_id=category_id,
        subcategory_id=subcategory_id,
        title=title,
        location=location,
        experience_level=experience_level,
        work_mode=work_mode,
        skill_ids=skill_id_list,
        min_salary=min_salary,
        max_salary=max_salary
    )
    
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
@handle_errors
async def search_full_time_jobs(
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    skill_ids: Optional[str] = Query(None, description="Comma-separated list of skill IDs"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
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
    
    skill_id_list = None
    if skill_ids:
        try:
            skill_id_list = [int(id.strip()) for id in skill_ids.split(',') if id.strip()]
        except ValueError:
            raise bad_request_error("Invalid skill_ids format. Use comma-separated integers.")
    
    jobs = job_repo.search_jobs(
        title=title,
        location=location,
        experience_level=experience_level,
        work_mode=work_mode,
        skill_ids=skill_id_list,
        category_id=category_id,
        subcategory_id=subcategory_id,
        min_salary=min_salary,
        max_salary=max_salary,
        skip=skip,
        limit=size,
        current_user_id=current_user.id if current_user else None
    )
    
    response_jobs = []
    for job in jobs:
        response_data = FullTimeJobResponse(**job)
        response_jobs.append(response_data)
    
    return FullTimeJobListResponse(
        jobs=response_jobs,
        total=len(response_jobs),
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
    
    jobs = job_repo.get_user_accessible_jobs(current_user.id, skip=skip, limit=size)
    total = job_repo.count_user_accessible_jobs(current_user.id)
    
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
@handle_errors
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
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    corporate_profile_ids = get_user_corporate_profiles(current_user.id, db)
    
    if not corporate_profile_ids:
        return UserFullTimeJobsResponse(
            user_jobs=[],
            total=0,
            page=page,
            size=size
        )
    
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


@router.get("/{job_id}", response_model=FullTimeJobResponse, tags=["Full Time Job"])
@handle_errors
async def get_full_time_job(
    job_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get full-time job by ID. Public access for ACTIVE jobs. Owners/team members can view any status."""
    print(f"[DEBUG GET] Getting job by id={job_id}, current_user={current_user.get('id') if current_user else None}")
    job_repo = FullTimeJobRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    team_repo = TeamMemberRepository(db)
    
    job_data = job_repo.get_by_id(job_id, current_user.get('id') if current_user else None)
    print(f"[DEBUG GET] Job found: {job_data is not None}, status={job_data.get('status') if job_data else 'N/A'}")
    validate_entity_exists(job_data, "Full-time job")
    
    corporate_profile_id = job_data['company_id']
    profile = corporate_repo.get_by_id(corporate_profile_id)
    validate_entity_exists(profile, "Corporate profile")
    
    # Allow viewing jobs even if profile is not active (for owners/team members)
    # Public users will be checked below
    # if not profile.is_active:
    #     raise not_found_error("Corporate profile is not active")
    
    is_owner_or_team_member = False
    if current_user:
        print(f"[DEBUG] current_user.id={current_user.get('id')}, profile.user_id={profile.user_id}")
        if profile.user_id == current_user.get('id'):
            is_owner_or_team_member = True
            print(f"[DEBUG] User is owner! is_owner_or_team_member=True")
        else:
            team_member = team_repo.get_by_user_and_corporate_profile(
                current_user.get('id'), corporate_profile_id
            )
            if team_member and team_member.status == TeamMemberStatus.ACCEPTED:
                is_owner_or_team_member = True
                print(f"[DEBUG] User is team member! is_owner_or_team_member=True")
    
    print(f"[DEBUG] is_owner_or_team_member={is_owner_or_team_member}, job_status={job_data.get('status', '')}")
    if not is_owner_or_team_member:
        job_status = job_data.get('status', '')
        if job_status != 'active':  # Fixed: status is lowercase in database
            print(f"[DEBUG] Job status is not active: {job_status} - returning 404")
            raise not_found_error("Full-time job not found")
    
    response_data = FullTimeJobResponse(**job_data)
    
    return response_data


@router.put("/{job_id}", response_model=FullTimeJobResponse, tags=["Full Time Job"])
@handle_errors
async def update_full_time_job(
    job_id: int,
    full_time_job: FullTimeJobUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update full-time job (requires UPDATE_JOB permission or admin)"""
    print(f"[DEBUG PUT] Updating job_id={job_id} by user={current_user.get('id')}")
    print(f"[DEBUG PUT] Update data: {full_time_job.model_dump(exclude_unset=True)}")
    
    if is_admin_user(current_user.get('email')):
        job_repo = FullTimeJobRepository(db)
        job_data = job_repo.get_by_id(job_id, current_user.get('id'))
        validate_entity_exists(job_data, "Full-time job")
    else:
        has_access, job_data, error_msg = check_job_access_permission(
            current_user.get('id'), job_id, Permission.UPDATE_JOB, db
        )
        
        if not has_access:
            if "not found" in error_msg.lower():
                raise not_found_error(error_msg)
            else:
                raise forbidden_error(error_msg)
    
    print(f"[DEBUG PUT] Current job status before update: {job_data.get('status')}")
    job_repo = FullTimeJobRepository(db)
    updated_job = job_repo.update(job_id, full_time_job)
    validate_entity_exists(updated_job, "Full-time job")
    print(f"[DEBUG PUT] Job updated successfully, new status: {updated_job.get('status')}")
    
    response_data = FullTimeJobResponse(**updated_job)
    
    return response_data


@router.delete("/{job_id}", response_model=MessageResponse, tags=["Full Time Job"])
@handle_errors
async def delete_full_time_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete full-time job (requires DELETE_JOB permission or admin)"""
    if is_admin_user(current_user.email):
        job_repo = FullTimeJobRepository(db)
        job_data = job_repo.get_by_id(job_id, current_user.id)
        validate_entity_exists(job_data, "Full-time job")
    else:
        has_access, job_data, error_msg = check_job_access_permission(
            current_user.id, job_id, Permission.DELETE_JOB, db
        )
        
        if not has_access:
            if "not found" in error_msg.lower():
                raise not_found_error(error_msg)
            else:
                raise forbidden_error(error_msg)
    
    job_repo = FullTimeJobRepository(db)
    success = job_repo.delete(job_id)
    if not success:
        raise bad_request_error("Failed to delete job")
    
    return MessageResponse(message="Full-time job deleted successfully")


@router.patch("/{job_id}/status", response_model=FullTimeJobResponse, tags=["Full Time Job"])
@handle_errors
async def change_job_status(
    job_id: int,
    new_status: str = Query(..., regex="^(ACTIVE|CLOSED|DRAFT)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change job status (requires UPDATE_JOB permission)"""
    has_access, job_data, error_msg = check_job_access_permission(
        current_user.id, job_id, Permission.UPDATE_JOB, db
    )
    
    if not has_access:
        if "not found" in error_msg.lower():
            raise not_found_error(error_msg)
        else:
            raise forbidden_error(error_msg)
    
    job_repo = FullTimeJobRepository(db)
    updated_job = job_repo.change_status(job_id, new_status)
    validate_entity_exists(updated_job, "Full-time job")
    
    response_data = FullTimeJobResponse(**updated_job)
    
    return response_data
