from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.repositories.gig_job_repository import GigJobRepository
from app.schemas.gig_job import (
    GigJobCreate, 
    GigJobUpdate, 
    GigJobResponse, 
    GigJobListResponse,
    GigJobSkillRemove
)
from app.schemas.common import SuccessResponse
from app.pagination import PaginationParams, create_pagination_response

router = APIRouter(prefix="/gig-jobs", tags=["Gig Jobs"])


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Get current user if authorization header is provided, otherwise return None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        # Import here to avoid circular imports
        from app.utils.auth import verify_token
        from app.repositories.user_repository import UserRepository
        from app.database import get_db
        
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


@router.post("/gig-job", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_gig_job(
    gig_job_data: GigJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new gig job post.
    
    - **title**: Job title (required)
    - **description**: Detailed job description (required)
    - **location_id**: Location ID (optional)
    - **experience_level**: Required experience level (entry_level, mid_level, junior, director)
    - **project_length**: Project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)
    - **skill_ids**: List of required skill IDs (e.g., [1, 2, 3])
    - **min_salary**: Minimum salary (required)
    - **max_salary**: Maximum salary (required)
    - **category_id**: Category id (required)
    - **subcategory_id**: Subcategory id (required)
    """
    repository = GigJobRepository(db)
    
    # Validate salary range
    if gig_job_data.min_salary >= gig_job_data.max_salary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum salary must be less than maximum salary"
        )
    
    gig_job = repository.create(gig_job_data, current_user.id)
    return SuccessResponse(
        msg="Gig job successfully added"
    )


@router.get("/", response_model=GigJobListResponse)
async def get_all_gig_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    project_length: Optional[str] = Query(None, description="Filter by project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)"),
    min_salary: Optional[float] = Query(None, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, description="Filter by maximum salary"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    date_posted: Optional[str] = Query(None, description="Filter by date posted (any_time, past_24_hours, past_week, past_month)"),
    sort_by: Optional[str] = Query("most_recent", description="Sort by (most_recent, most_relevant)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get all gig jobs with advanced filtering and pagination.
    Authentication is optional - if Authorization header is provided, it will be validated.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    - **status_filter**: Optional status filter
    - **experience_level**: Filter by experience level (entry_level, mid_level, junior, director)
    - **project_length**: Filter by project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)
    - **min_salary**: Filter by minimum salary
    - **max_salary**: Filter by maximum salary
    - **location_id**: Filter by location ID
    - **category_id**: Filter by category ID
    - **subcategory_id**: Filter by subcategory ID
    - **date_posted**: Filter by date posted (any_time, past_24_hours, past_week, past_month)
    - **sort_by**: Sort by (most_recent, most_relevant)
    - **Authorization**: Optional Bearer token for authentication
    """
    repository = GigJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    gig_jobs, total = repository.get_all_gig_jobs(
        pagination=pagination,
        status=status_filter,
        experience_level=experience_level,
        project_length=project_length,
        min_salary=min_salary,
        max_salary=max_salary,
        location_id=location_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
        date_posted=date_posted,
        sort_by=sort_by,
        current_user_id=current_user.id if current_user else None
    )
    
    return create_pagination_response(
        items=gig_jobs,
        total=total,
        pagination=pagination
    )


@router.get("/my-jobs", response_model=GigJobListResponse)
async def get_my_gig_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    project_length: Optional[str] = Query(None, description="Filter by project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)"),
    min_salary: Optional[float] = Query(None, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, description="Filter by maximum salary"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    date_posted: Optional[str] = Query(None, description="Filter by date posted (any_time, past_24_hours, past_week, past_month)"),
    sort_by: Optional[str] = Query("most_recent", description="Sort by (most_recent, most_relevant)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get gig jobs created by the current user with advanced filtering.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    - **status_filter**: Optional status filter
    - **experience_level**: Filter by experience level (entry_level, mid_level, junior, director)
    - **project_length**: Filter by project length (LESS_THAN_ONE_MONTH, ONE_TO_THREE_MONTHS, THREE_TO_SIX_MONTHS, MORE_THAN_SIX_MONTHS)
    - **min_salary**: Filter by minimum salary
    - **max_salary**: Filter by maximum salary
    - **location_id**: Filter by location ID
    - **category_id**: Filter by category ID
    - **subcategory_id**: Filter by subcategory ID
    - **date_posted**: Filter by date posted (any_time, past_24_hours, past_week, past_month)
    - **sort_by**: Sort by (most_recent, most_relevant)
    """
    repository = GigJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    gig_jobs, total = repository.get_user_gig_jobs_with_filters(
        user_id=current_user.id,
        pagination=pagination,
        status=status_filter,
        experience_level=experience_level,
        project_length=project_length,
        min_salary=min_salary,
        max_salary=max_salary,
        location_id=location_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
        date_posted=date_posted,
        sort_by=sort_by,
        current_user_id=current_user.id
    )
    
    return create_pagination_response(
        items=gig_jobs,
        total=total,
        pagination=pagination
    )


@router.get("/{gig_job_id}", response_model=GigJobResponse)
async def get_gig_job_by_id(
    gig_job_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get a specific gig job by ID.
    
    - **gig_job_id**: ID of the gig job
    - **Authorization**: Optional Bearer token for authentication
    """
    repository = GigJobRepository(db)
    gig_job = repository.get_by_id(gig_job_id, current_user.id if current_user else None)
    
    if not gig_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig job not found"
        )
    
    return gig_job


@router.put("/{gig_job_id}", response_model=SuccessResponse)
async def update_gig_job(
    gig_job_id: int,
    gig_job_data: GigJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a gig job (only by the author). New skills will be added to existing ones.
    
    - **gig_job_id**: ID of the gig job to update
    - **skill_ids**: List of skill IDs to add (will not remove existing skills)
    """
    repository = GigJobRepository(db)
    
    # Validate salary range if both are provided
    if gig_job_data.min_salary is not None and gig_job_data.max_salary is not None:
        if gig_job_data.min_salary >= gig_job_data.max_salary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum salary must be less than maximum salary"
            )
    
    updated_gig_job = repository.update(gig_job_id, gig_job_data, current_user.id)
    
    if not updated_gig_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig job not found or you don't have permission to update it"
        )
    
    return SuccessResponse(
        msg="Gig job successfully updated"
    )


@router.delete("/{gig_job_id}", response_model=SuccessResponse)
async def delete_gig_job(
    gig_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a gig job (only by the author).
    
    - **gig_job_id**: ID of the gig job to delete
    """
    repository = GigJobRepository(db)
    
    success = repository.delete(gig_job_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig job not found or you don't have permission to delete it"
        )
    
    return SuccessResponse(
        msg="Gig job successfully deleted"
    )


@router.delete("/{gig_job_id}/skills", response_model=SuccessResponse)
async def remove_gig_job_skill(
    gig_job_id: int,
    skill_data: GigJobSkillRemove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a GigJobSkill relationship from a gig job (only by the author).
    
    - **gig_job_id**: ID of the gig job (from URL)
    - **gig_job_skill_id**: GigJobSkill ID to remove (from body)
    
    Example request body:
    {
        "gig_job_skill_id": 48
    }
    """
    repository = GigJobRepository(db)
    
    try:
        result = repository.remove_gig_job_skill(
            gig_job_id=gig_job_id,
            gig_job_skill_id=skill_data.gig_job_skill_id,
            user_id=current_user.id
        )
        
        return SuccessResponse(
            msg=result["message"],
            data={
                "gig_job": result["gig_job"],
                "removed_skill": result["removed_skill"],
                "removed_gig_job_skill_id": result["removed_gig_job_skill_id"]
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing gig job skill: {str(e)}"
        )


@router.get("/filter/search", response_model=GigJobListResponse)
async def search_gig_jobs(
    q: str = Query(..., min_length=2, description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Search gig jobs by title, description, or skills.
    
    - **q**: Search term (minimum 2 characters)
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = GigJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    gig_jobs, total = repository.search_gig_jobs(q, pagination, current_user.id if current_user else None)
    
    return create_pagination_response(
        items=gig_jobs,
        total=total,
        pagination=pagination
    )