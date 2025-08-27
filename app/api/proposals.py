from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.repositories.proposal_repository import ProposalRepository
from app.repositories.gig_job_repository import GigJobRepository
from app.schemas.proposal import (
    ProposalCreate, 
    ProposalUpdate, 
    ProposalResponse, 
    ProposalListResponse
)
from app.repositories.full_time_job_repository import FullTimeJobRepository
from app.pagination import PaginationParams, create_pagination_response

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("/", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a proposal for a gig job or full-time job.
    
    - **cover_letter**: Your cover letter explaining why you're the best fit
    - **attachments**: Optional file attachments (JSON string)
    - **gig_job_id**: ID of the gig job you're applying for (for gig jobs)
    - **full_time_job_id**: ID of the full-time job you're applying for (for full-time jobs)
    """
    repository = ProposalRepository(db)
    
    if proposal_data.gig_job_id:
        # Proposal for gig job
        gig_job_repository = GigJobRepository(db)
        gig_job = gig_job_repository.get_by_id(proposal_data.gig_job_id)
        if not gig_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gig job not found"
            )
        
        # Check if user is not the author of the gig job
        if gig_job.author_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot submit a proposal to your own gig job"
            )
        
        # Check if user has already submitted a proposal for this gig job
        if repository.check_user_proposal_exists(current_user.id, proposal_data.gig_job_id, "gig"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted a proposal for this gig job"
            )
    
    elif proposal_data.full_time_job_id:
        # Proposal for full-time job
        full_time_job_repository = FullTimeJobRepository(db)
        full_time_job = full_time_job_repository.get_by_id(proposal_data.full_time_job_id)
        if not full_time_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Full-time job not found"
            )
        
        # Check if user has already submitted a proposal for this full-time job
        if repository.check_user_proposal_exists(current_user.id, proposal_data.full_time_job_id, "full_time"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted a proposal for this full-time job"
            )
    
    proposal = repository.create(proposal_data, current_user.id)
    return proposal


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal_by_id(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific proposal by ID.
    
    - **proposal_id**: ID of the proposal
    """
    repository = ProposalRepository(db)
    proposal = repository.get_by_id(proposal_id)
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    # Check if user has permission to view this proposal
    if proposal.user_id != current_user.id:
        # Check if user is the author of the gig job
        gig_job_repository = GigJobRepository(db)
        gig_job = gig_job_repository.get_by_id(proposal.gig_job_id)
        if not gig_job or gig_job.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this proposal"
            )
    
    return proposal


@router.get("/my-proposals", response_model=ProposalListResponse)
async def get_my_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get proposals submitted by the current user.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_user_proposals(current_user.id, pagination)
    
    return create_pagination_response(
        items=proposals,
        total=total,
        pagination=pagination
    )


@router.get("/gig-job/{gig_job_id}", response_model=ProposalListResponse)
async def get_gig_job_proposals(
    gig_job_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all proposals for a specific gig job (only by the gig job author).
    
    - **gig_job_id**: ID of the gig job
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    gig_job_repository = GigJobRepository(db)
    gig_job = gig_job_repository.get_by_id(gig_job_id)
    
    if not gig_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig job not found"
        )
    
    # Check if user is the author of the gig job
    if gig_job.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view proposals for your own gig jobs"
        )
    
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_gig_job_proposals(gig_job_id, pagination)
    
    return create_pagination_response(
        items=proposals,
        total=total,
        pagination=pagination
    )


@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: int,
    proposal_data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a proposal (only by the author).
    
    - **proposal_id**: ID of the proposal to update
    """
    repository = ProposalRepository(db)
    
    updated_proposal = repository.update(proposal_id, proposal_data, current_user.id)
    
    if not updated_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found or you don't have permission to update it"
        )
    
    return updated_proposal


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a proposal (only by the author).
    
    - **proposal_id**: ID of the proposal to delete
    """
    repository = ProposalRepository(db)
    
    success = repository.delete(proposal_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found or you don't have permission to delete it"
        )
