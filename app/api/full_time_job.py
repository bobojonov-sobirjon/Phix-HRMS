from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..repositories.full_time_job_repository import FullTimeJobRepository
from ..repositories.corporate_profile_repository import CorporateProfileRepository
from ..schemas.full_time_job import (
    FullTimeJobCreate,
    FullTimeJobUpdate,
    FullTimeJobResponse,
    FullTimeJobListResponse,
    UserFullTimeJobsResponse
)
from ..schemas.common import MessageResponse, SuccessResponse
from ..utils.auth import get_current_user

router = APIRouter(prefix="/full-time-jobs", tags=["Full Time Job"])


@router.post("/", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def create_full_time_job(
    full_time_job: FullTimeJobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new full-time job"""
    corporate_repo = CorporateProfileRepository(db)
    job_repo = FullTimeJobRepository(db)
    
    # Check if user has a verified corporate profile
    profile = corporate_repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate profile required to create full-time jobs"
        )
    
    if not profile.is_verified or not profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corporate profile must be verified and active to create jobs"
        )
    
    # Create the job
    db_job = job_repo.create(full_time_job, profile.id)
    
    # Add company name to response
    db_job["company_name"] = profile.company_name
    
    return db_job


@router.get("/", response_model=FullTimeJobListResponse, tags=["Full Time Job"])
async def get_all_full_time_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all full-time jobs with pagination"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    jobs = job_repo.get_all_active(skip=skip, limit=size)
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
    min_salary: Optional[float] = Query(None, ge=0),
    max_salary: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search full-time jobs with filters"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    jobs = job_repo.search_jobs(
        title=title,
        location=location,
        experience_level=experience_level,
        work_mode=work_mode,
        min_salary=min_salary,
        max_salary=max_salary,
        skip=skip,
        limit=size
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
    """Get current user's full-time jobs"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    jobs = job_repo.get_by_user_id(current_user.id, skip=skip, limit=size)
    total = job_repo.count_by_user(current_user.id)
    
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
    status: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_salary: Optional[float] = Query(None, ge=0, description="Filter by minimum salary"),
    max_salary: Optional[float] = Query(None, ge=0, description="Filter by maximum salary"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's full-time jobs with advanced filtering"""
    job_repo = FullTimeJobRepository(db)
    skip = (page - 1) * size
    
    # Get filtered jobs
    jobs = job_repo.get_by_user_id_with_filters(
        user_id=current_user.id,
        skip=skip,
        limit=size,
        status=status,
        job_type=job_type,
        experience_level=experience_level,
        work_mode=work_mode,
        location=location,
        min_salary=min_salary,
        max_salary=max_salary
    )
    
    total = job_repo.count_by_user_with_filters(
        user_id=current_user.id,
        status=status,
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


@router.get("/{job_id}", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def get_full_time_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get full-time job by ID"""
    job_repo = FullTimeJobRepository(db)
    job = job_repo.get_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Full-time job not found"
        )
    
    # Convert dict response to FullTimeJobResponse object
    response_data = FullTimeJobResponse(**job)
    
    return response_data


@router.put("/{job_id}", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def update_full_time_job(
    job_id: int,
    full_time_job: FullTimeJobUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update full-time job"""
    job_repo = FullTimeJobRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if job exists
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Full-time job not found"
        )
    
    # Check if user owns the company that posted this job
    profile = corporate_repo.get_by_id(job.company_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Update the job
    updated_job = job_repo.update(job_id, full_time_job)
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )
    
    # Convert dict response to FullTimeJobResponse object
    response_data = FullTimeJobResponse(**updated_job)
    
    return response_data


@router.delete("/{job_id}", response_model=MessageResponse, tags=["Full Time Job"])
async def delete_full_time_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete full-time job"""
    job_repo = FullTimeJobRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if job exists
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Full-time job not found"
        )
    
    # Check if user owns the company that posted this job
    profile = corporate_repo.get_by_id(job.company_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    # Delete the job
    success = job_repo.delete(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )
    
    return MessageResponse(message="Full-time job deleted successfully")


@router.patch("/{job_id}/status", response_model=FullTimeJobResponse, tags=["Full Time Job"])
async def change_job_status(
    job_id: int,
    status: str = Query(..., regex="^(active|closed|draft)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change job status"""
    job_repo = FullTimeJobRepository(db)
    corporate_repo = CorporateProfileRepository(db)
    
    # Check if job exists
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Full-time job not found"
        )
    
    # Check if user owns the company that posted this job
    profile = corporate_repo.get_by_id(job.company_id)
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change this job's status"
        )
    
    # Change status
    updated_job = job_repo.change_status(job_id, status)
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change job status"
        )
    
    # Convert dict response to FullTimeJobResponse object
    response_data = FullTimeJobResponse(**updated_job)
    
    return response_data
