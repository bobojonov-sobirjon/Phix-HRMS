from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..repositories.job_post_type_repository import JobPostTypeRepository
from ..schemas.job_post_type import JobPostType, JobPostTypeCreate, JobPostTypeUpdate
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/job-post-types", tags=["Job Post Types"])

@router.post("/gig-job", response_model=JobPostType, status_code=status.HTTP_201_CREATED)
def create_gig_job_post_type(
    job_post_type: JobPostTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new gig job post type"""
    try:
        repository = JobPostTypeRepository(db)
        return repository.create(job_post_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[JobPostType])
def get_all_job_post_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all job post types"""
    try:
        repository = JobPostTypeRepository(db)
        return repository.get_all(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_post_type_id}", response_model=JobPostType)
def get_job_post_type_by_id(
    job_post_type_id: int,
    db: Session = Depends(get_db)
):
    """Get job post type by ID"""
    try:
        repository = JobPostTypeRepository(db)
        job_post_type = repository.get_by_id(job_post_type_id)
        if not job_post_type:
            raise HTTPException(
                status_code=404,
                detail="Job post type not found"
            )
        return job_post_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{job_post_type_id}", response_model=JobPostType)
def update_job_post_type(
    job_post_type_id: int,
    job_post_type: JobPostTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update job post type"""
    try:
        repository = JobPostTypeRepository(db)
        updated_job_post_type = repository.update(job_post_type_id, job_post_type)
        if not updated_job_post_type:
            raise HTTPException(
                status_code=404,
                detail="Job post type not found"
            )
        return updated_job_post_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{job_post_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_post_type(
    job_post_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete job post type"""
    try:
        repository = JobPostTypeRepository(db)
        success = repository.delete(job_post_type_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Job post type not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 