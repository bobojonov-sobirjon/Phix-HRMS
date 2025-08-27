from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    GigJobListResponse
)
from app.pagination import PaginationParams, create_pagination_response

router = APIRouter(prefix="/gig-jobs", tags=["Gig Jobs"])


@router.post("/gig-job", response_model=GigJobResponse, status_code=status.HTTP_201_CREATED)
async def create_gig_job(
    gig_job_data: GigJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new gig job post.
    
    - **title**: Job title (required)
    - **description**: Detailed job description (required)
    - **location**: Job location (required)
    - **experience_level**: Required experience level (entry_level, mid_level, junior, director)
    - **skill_names**: List of required skill names (e.g., ["Python", "JavaScript", "React"])
    - **min_salary**: Minimum salary (required)
    - **max_salary**: Maximum salary (required)
    - **deadline_days**: Deadline in days (required)
    """
    repository = GigJobRepository(db)
    
    # Validate salary range
    if gig_job_data.min_salary >= gig_job_data.max_salary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum salary must be less than maximum salary"
        )
    
    gig_job_data = repository.create(gig_job_data, current_user.id)
    return gig_job_data


@router.get("/", response_model=GigJobListResponse)
async def get_all_gig_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode"),
    remote_only: Optional[bool] = Query(None, description="Filter by remote only"),
    min_salary: Optional[float] = Query(None, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, description="Filter by maximum salary"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db: Session = Depends(get_db)
):
    """
    Get all gig jobs with advanced filtering and pagination.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    - **status_filter**: Optional status filter
    - **job_type**: Filter by job type (full_time, part_time, freelance, internship)
    - **experience_level**: Filter by experience level (entry_level, mid_level, junior, director)
    - **work_mode**: Filter by work mode (on_site, remote, hybrid, flexible_hours)
    - **remote_only**: Filter by remote only option
    - **min_salary**: Filter by minimum salary
    - **max_salary**: Filter by maximum salary
    - **location**: Filter by location (partial match)
    """
    repository = GigJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    gig_jobs, total = repository.get_all_gig_jobs(
        pagination=pagination,
        status=status_filter,
        job_type=job_type,
        experience_level=experience_level,
        work_mode=work_mode,
        remote_only=remote_only,
        min_salary=min_salary,
        max_salary=max_salary,
        location=location
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
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode"),
    remote_only: Optional[bool] = Query(None, description="Filter by remote only"),
    min_salary: Optional[float] = Query(None, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, description="Filter by maximum salary"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get gig jobs created by the current user with advanced filtering.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    - **status_filter**: Optional status filter
    - **job_type**: Filter by job type (full_time, part_time, freelance, internship)
    - **experience_level**: Filter by experience level (entry_level, mid_level, junior, director)
    - **work_mode**: Filter by work mode (on_site, remote, hybrid, flexible_hours)
    - **remote_only**: Filter by remote only option
    - **min_salary**: Filter by minimum salary
    - **max_salary**: Filter by maximum salary
    - **location**: Filter by location (partial match)
    """
    repository = GigJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    gig_jobs, total = repository.get_user_gig_jobs_with_filters(
        user_id=current_user.id,
        pagination=pagination,
        status=status_filter,
        job_type=job_type,
        experience_level=experience_level,
        work_mode=work_mode,
        remote_only=remote_only,
        min_salary=min_salary,
        max_salary=max_salary,
        location=location
    )
    
    return create_pagination_response(
        items=gig_jobs,
        total=total,
        pagination=pagination
    )


@router.get("/{gig_job_id}", response_model=GigJobResponse)
async def get_gig_job_by_id(
    gig_job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific gig job by ID.
    
    - **gig_job_id**: ID of the gig job
    """
    repository = GigJobRepository(db)
    gig_job = repository.get_by_id(gig_job_id)
    
    if not gig_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig job not found"
        )
    
    return gig_job


@router.put("/{gig_job_id}", response_model=GigJobResponse)
async def update_gig_job(
    gig_job_id: int,
    gig_job_data: GigJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a gig job (only by the author).
    
    - **gig_job_id**: ID of the gig job to update
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
    
    return updated_gig_job


@router.delete("/{gig_job_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/filter/search", response_model=GigJobListResponse)
async def search_gig_jobs(
    q: str = Query(..., min_length=2, description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Search gig jobs by title, description, or skills.
    
    - **q**: Search term (minimum 2 characters)
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = GigJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    gig_jobs, total = repository.search_gig_jobs(q, pagination)
    
    return create_pagination_response(
        items=gig_jobs,
        total=total,
        pagination=pagination
    )
