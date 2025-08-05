from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..repositories.job_repository import JobRepository
from ..schemas.job import Job, JobCreate, JobUpdate, JobFilter
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/gig-job", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_gig_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new gig job"""
    try:
        # Set user_id from current user
        job.user_id = current_user.id
        
        # Ensure this is a gig job (job_post_type_id should be for gig job)
        # You can add validation here if needed
        
        repository = JobRepository(db)
        return repository.create(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Job])
def get_all_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all jobs (without filtering)"""
    try:
        repository = JobRepository(db)
        return repository.get_all(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-jobs", response_model=List[Job])
def get_my_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's jobs (without filtering)"""
    try:
        repository = JobRepository(db)
        return repository.get_by_user_id(current_user.id, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=Job)
def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get job by ID"""
    try:
        repository = JobRepository(db)
        job = repository.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_id}", response_model=Job)
def update_job(
    job_id: int,
    job: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update job"""
    try:
        repository = JobRepository(db)
        # Check if job belongs to current user
        existing_job = repository.get_by_id(job_id)
        if not existing_job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        if existing_job.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update this job"
            )
        
        updated_job = repository.update(job_id, job)
        return updated_job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete job"""
    try:
        repository = JobRepository(db)
        # Check if job belongs to current user
        existing_job = repository.get_by_id(job_id)
        if not existing_job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        if existing_job.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this job"
            )
        
        success = repository.delete(job_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filter/search", response_model=List[Job])
def filter_jobs(
    job_name: Optional[str] = Query(None, description="Filter by job name"),
    location_ids: Optional[str] = Query(None, description="Comma-separated location IDs"),
    price_min: Optional[float] = Query(None, description="Minimum salary"),
    price_max: Optional[float] = Query(None, description="Maximum salary"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    work_mode: Optional[str] = Query(None, description="Work mode"),
    job_type: Optional[str] = Query(None, description="Job type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Filter jobs by various criteria (separate endpoint for filtering)"""
    try:
        repository = JobRepository(db)
        
        # Parse location_ids if provided
        location_ids_list = None
        if location_ids:
            try:
                location_ids_list = [int(x.strip()) for x in location_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid location_ids format. Use comma-separated integers."
                )
        
        return repository.filter_jobs(
            job_name=job_name,
            location_ids=location_ids_list,
            price_min=price_min,
            price_max=price_max,
            experience_level=experience_level,
            work_mode=work_mode,
            job_type=job_type,
            skip=skip,
            limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 