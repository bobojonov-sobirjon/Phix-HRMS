from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.auth import get_current_user
from app.utils.decorators import handle_errors
from app.utils.response_helpers import not_found_error, bad_request_error
from app.models.user import User
from app.repositories.saved_job_repository import SavedJobRepository
from app.schemas.saved_job import (
    SavedJobCreate, 
    SavedJobResponse, 
    SavedJobListResponse,
    SavedJobDetailedResponse,
    SavedJobDetailedListResponse
)
from app.pagination import PaginationParams, create_pagination_response

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SavedJobResponse)
@handle_errors
async def save_job(
    saved_job_data: SavedJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a job (either gig job or full-time job).
    
    - **gig_job_id**: ID of the gig job to save (optional)
    - **full_time_job_id**: ID of the full-time job to save (optional)
    
    Note: Either gig_job_id or full_time_job_id must be provided, but not both.
    """
    repository = SavedJobRepository(db)
    try:
        saved_job = repository.create(saved_job_data, current_user.id)
        return SavedJobResponse.from_orm(saved_job)
    except ValueError as e:
        raise bad_request_error(str(e))


@router.get("/", response_model=SavedJobDetailedListResponse)
async def get_my_saved_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all saved jobs by the current user with full details.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = SavedJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    saved_jobs, total = repository.get_user_saved_jobs(current_user.id, pagination)
    
    # Convert saved jobs to detailed response format
    saved_job_responses = [SavedJobDetailedResponse.from_orm(saved_job, db, current_user.id) for saved_job in saved_jobs]
    
    return create_pagination_response(
        items=saved_job_responses,
        total=total,
        pagination=pagination
    )


@router.get("/gig-jobs", response_model=SavedJobDetailedListResponse)
@handle_errors
async def get_my_saved_gig_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get saved gig jobs by the current user with full details.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = SavedJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    saved_jobs, total = repository.get_user_saved_gig_jobs(current_user.id, pagination)
    
    # Convert saved jobs to detailed response format
    saved_job_responses = [SavedJobDetailedResponse.from_orm(saved_job, db, current_user.id) for saved_job in saved_jobs]
    
    return create_pagination_response(
        items=saved_job_responses,
        total=total,
        pagination=pagination
    )


@router.get("/full-time-jobs", response_model=SavedJobDetailedListResponse)
async def get_my_saved_full_time_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get saved full-time jobs by the current user with full details.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = SavedJobRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    saved_jobs, total = repository.get_user_saved_full_time_jobs(current_user.id, pagination)
    
    # Convert saved jobs to detailed response format
    saved_job_responses = [SavedJobDetailedResponse.from_orm(saved_job, db, current_user.id) for saved_job in saved_jobs]
    
    return create_pagination_response(
        items=saved_job_responses,
        total=total,
        pagination=pagination
    )


@router.delete("/{saved_job_id}")
@handle_errors
async def unsave_job(
    saved_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a saved job by ID.
    
    - **saved_job_id**: ID of the saved job to remove
    """
    repository = SavedJobRepository(db)
    success = repository.delete(saved_job_id, current_user.id)
    
    if not success:
        raise not_found_error("Saved job not found or you don't have permission to delete it")
    
    return {"status": "success", "msg": "Job unsaved successfully"}


@router.delete("/gig-job/{gig_job_id}")
@handle_errors
async def unsave_gig_job(
    gig_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a saved gig job by gig job ID.
    
    - **gig_job_id**: ID of the gig job to unsave
    """
    repository = SavedJobRepository(db)
    success = repository.delete_by_job(current_user.id, gig_job_id=gig_job_id)
    
    if not success:
        raise not_found_error("Gig job is not saved or you don't have permission to unsave it")
    
    return {"status": "success", "msg": "Gig job unsaved successfully"}


@router.delete("/full-time-job/{full_time_job_id}")
@handle_errors
async def unsave_full_time_job(
    full_time_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a saved full-time job by full-time job ID.
    
    - **full_time_job_id**: ID of the full-time job to unsave
    """
    repository = SavedJobRepository(db)
    success = repository.delete_by_job(current_user.id, full_time_job_id=full_time_job_id)
    
    if not success:
        raise not_found_error("Full-time job is not saved or you don't have permission to unsave it")
    
    return {"status": "success", "msg": "Full-time job unsaved successfully"}
