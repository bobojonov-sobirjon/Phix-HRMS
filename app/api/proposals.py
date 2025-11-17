from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.user_device_token import UserDeviceToken
from app.repositories.proposal_repository import ProposalRepository
from app.repositories.proposal_attachment_repository import ProposalAttachmentRepository
from app.repositories.gig_job_repository import GigJobRepository
from app.schemas.proposal import (
    ProposalCreate, 
    ProposalUpdate, 
    ProposalResponse, 
    ProposalListResponse,
    ProposalCreateForm,
    ProposalUpdateForm,
    ProposalAttachmentResponse
)
from app.repositories.full_time_job_repository import FullTimeJobRepository
from app.pagination import PaginationParams, create_pagination_response
from app.utils.firebase_notifications import send_push_notification_multiple
import json
import os
from typing import List, Optional

router = APIRouter(prefix="/proposals", tags=["Proposals"])

# File upload directory
UPLOAD_DIR = "static/proposals"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_user_device_tokens(db: Session, user_id: int) -> List[str]:
    """Get all active device tokens for a user"""
    device_tokens = db.query(UserDeviceToken).filter(
        UserDeviceToken.user_id == user_id,
        UserDeviceToken.is_active == True
    ).all()
    return [token.device_token for token in device_tokens]


def send_proposal_notification(
    db: Session,
    recipient_user_id: int,
    title: str,
    body: str,
    data: dict
):
    """Send push notification to user's devices"""
    try:
        device_tokens = get_user_device_tokens(db, recipient_user_id)
        print(f"DEBUG: Found {len(device_tokens)} device token(s) for user_id={recipient_user_id}")
        if device_tokens:
            print(f"DEBUG: Sending notification - Title: {title}, Body: {body}")
            result = send_push_notification_multiple(
                device_tokens=device_tokens,
                title=title,
                body=body,
                data={str(k): str(v) for k, v in data.items()}
            )
            print(f"DEBUG: Notification result - Success: {result.get('success_count', 0)}, Failed: {result.get('failure_count', 0)}")
        else:
            print(f"DEBUG: No device tokens found for user_id={recipient_user_id}")
    except Exception as e:
        print(f"ERROR: Failed to send notification to user_id={recipient_user_id}: {str(e)}")
        import traceback
        traceback.print_exc()


def save_uploaded_files(files: List[UploadFile], user_id: int, proposal_id: int) -> List[dict]:
    """Save uploaded files and return list of file info"""
    file_info_list = []
    
    for file in files:
        if file.filename:
            # Create user-specific directory
            user_dir = os.path.join(UPLOAD_DIR, f"user_{user_id}")
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"proposal_{proposal_id}_{file.filename}"
            file_path = os.path.join(user_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            # Store relative path for database
            relative_path = os.path.join("proposals", f"user_{user_id}", unique_filename)
            
            # Get file size
            file_size = len(content)
            
            file_info_list.append({
                "attachment": relative_path,
                "size": file_size,
                "name": file.filename
            })
    
    return file_info_list


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_proposal(
    cover_letter: str = Form(..., min_length=10, description="Cover letter content"),
    delivery_time: Optional[int] = Form(None, ge=1, description="Delivery time in days"),
    offer_amount: Optional[float] = Form(None, ge=0, description="Offer amount in currency"),
    gig_job_id: Optional[int] = Form(None, description="ID of the gig job (for gig jobs)"),
    full_time_job_id: Optional[int] = Form(None, description="ID of the full-time job (for full-time jobs)"),
    attachments: List[UploadFile] = File(None, description="File attachments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a proposal for a gig job or full-time job with file attachments.
    
    - **cover_letter**: Your cover letter explaining why you're the best fit
    - **delivery_time**: Delivery time in days (optional)
    - **offer_amount**: Offer amount in currency (optional)
    - **attachments**: Optional file attachments (multiple files supported)
    - **gig_job_id**: ID of the gig job you're applying for (for gig jobs)
    - **full_time_job_id**: ID of the full-time job you're applying for (for full-time jobs)
    """
    # Validate that either gig_job_id or full_time_job_id is provided
    if not gig_job_id and not full_time_job_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "msg": "Either gig_job_id or full_time_job_id must be provided"
            }
        )
    
    if gig_job_id and full_time_job_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "msg": "Only one of gig_job_id or full_time_job_id can be provided"
            }
        )
    
    repository = ProposalRepository(db)
    attachment_repository = ProposalAttachmentRepository(db)
    
    if gig_job_id:
        # Proposal for gig job
        gig_job_repository = GigJobRepository(db)
        gig_job = gig_job_repository.get_by_id(gig_job_id)
        if not gig_job:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "msg": "Gig job not found"
                }
            )
        
        # Check if user is not the author of the gig job
        if gig_job['author']['id'] == current_user.id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "msg": "You cannot submit a proposal to your own gig job"
                }
            )
        
        # Check if user has already submitted a proposal for this gig job
        if repository.check_user_proposal_exists(current_user.id, gig_job_id, "gig"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "msg": "You have already submitted a proposal for this gig job"
                }
            )
    
    elif full_time_job_id:
        # Proposal for full-time job
        full_time_job_repository = FullTimeJobRepository(db)
        full_time_job = full_time_job_repository.get_object_by_id(full_time_job_id)
        if not full_time_job:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": "error",
                    "msg": "Full-time job not found"
                }
            )
        
        # Check if user has already submitted a proposal for this full-time job
        if repository.check_user_proposal_exists(current_user.id, full_time_job_id, "full_time"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "msg": "You have already submitted a proposal for this full-time job"
                }
            )
    
    # Create proposal data
    proposal_data = ProposalCreate(
        cover_letter=cover_letter,
        delivery_time=delivery_time,
        offer_amount=offer_amount,
        gig_job_id=gig_job_id,
        full_time_job_id=full_time_job_id
    )
    
    # Create proposal first to get ID
    proposal = repository.create(proposal_data, current_user.id)
    
    # Process file uploads if any
    if attachments:
        file_info_list = save_uploaded_files(attachments, current_user.id, proposal.id)
        for file_info in file_info_list:
            attachment_repository.create(
                proposal_id=proposal.id,
                attachment=file_info["attachment"],
                size=file_info["size"],
                name=file_info["name"]
            )
    
    # Get the created proposal with all relationships for response
    proposal_with_details = repository.get_by_id(proposal.id)
    
    # Determine job type and ID for success message and notification
    job_type = "gig job" if gig_job_id else "full-time job"
    job_id = gig_job_id if gig_job_id else full_time_job_id
    
    # Send push notification to job owner (Application notification)
    try:
        job_owner_id = None
        job_title = None
        
        if gig_job_id:
            # Get gig job directly from database to ensure we have author_id
            from app.models.gig_job import GigJob
            gig_job_model = db.query(GigJob).filter(GigJob.id == gig_job_id).first()
            if gig_job_model:
                job_owner_id = gig_job_model.author_id
                job_title = gig_job_model.title
        elif full_time_job_id:
            full_time_job_repository = FullTimeJobRepository(db)
            full_time_job = full_time_job_repository.get_object_by_id(full_time_job_id)
            if full_time_job:
                job_owner_id = full_time_job.created_by_user_id
                job_title = full_time_job.title
        
        if job_owner_id and job_owner_id != current_user.id:
            applicant_name = current_user.name or current_user.email or "Someone"
            position_name = job_title or "position"
            
            title = "New Application Received"
            body = f"{applicant_name} applied for {position_name} position"
            
            send_proposal_notification(
                db=db,
                recipient_user_id=job_owner_id,
                title=title,
                body=body,
                data={
                    "type": "application",
                    "proposal_id": str(proposal.id),
                    "job_id": str(job_id),
                    "job_type": "gig" if gig_job_id else "full_time",
                    "applicant_id": str(current_user.id)
                }
            )
    except Exception:
        pass
    
    try:
        # Create response data with expanded job details
        response_data = ProposalResponse.from_orm(proposal_with_details)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "msg": f"Proposal successfully submitted for {job_type} (ID: {job_id})",
                "data": response_data.model_dump(mode='json')
            }
        )
    except Exception as e:
        # If there's an error with the detailed response, return basic response
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "msg": f"Proposal successfully submitted for {job_type} (ID: {job_id})",
                "data": {
                    "id": proposal.id,
                    "user_id": proposal.user_id,
                    "gig_job_id": proposal.gig_job_id,
                    "full_time_job_id": proposal.full_time_job_id,
                    "cover_letter": proposal.cover_letter,
                    "delivery_time": proposal.delivery_time,
                    "offer_amount": proposal.offer_amount,
                    "attachments": [],
                    "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
                    "updated_at": proposal.updated_at.isoformat() if proposal.updated_at else None
                }
            }
        )


@router.get("/my-proposals-gig-job", response_model=ProposalListResponse)
async def get_my_gig_job_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get gig job proposals submitted by the current user.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_user_gig_job_proposals(current_user.id, pagination)
    
    # Convert proposals to response format
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


@router.get("/my-proposals-full-time-jobs", response_model=ProposalListResponse)
async def get_my_full_time_job_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full-time job proposals submitted by the current user.
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_user_full_time_job_proposals(current_user.id, pagination)
    
    # Convert proposals to response format
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


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
    is_job_owner = False
    if proposal.user_id != current_user.id:
        # Check if user is the author of the gig job or full-time job
        has_permission = False
        
        if proposal.gig_job_id:
            gig_job_repository = GigJobRepository(db)
            gig_job = gig_job_repository.get_by_id(proposal.gig_job_id)
            if gig_job and gig_job['author']['id'] == current_user.id:
                has_permission = True
                is_job_owner = True
        elif proposal.full_time_job_id:
            full_time_job_repository = FullTimeJobRepository(db)
            full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
            if full_time_job and full_time_job.created_by_user_id == current_user.id:
                has_permission = True
                is_job_owner = True
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this proposal"
            )
    
    # If job owner is viewing the proposal and it's not read yet, mark as read and send notification
    if is_job_owner and not proposal.is_read:
        # Mark proposal as read
        repository.mark_as_read(proposal_id)
        
        # Send push notification to proposal sender (My Proposal notification)
        try:
            proposal_sender_id = proposal.user_id
            job_title = None
            
            if proposal.gig_job_id:
                gig_job_repository = GigJobRepository(db)
                gig_job = gig_job_repository.get_by_id(proposal.gig_job_id)
                if gig_job:
                    job_title = gig_job.get('title', 'gig job')
            elif proposal.full_time_job_id:
                full_time_job_repository = FullTimeJobRepository(db)
                full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
                if full_time_job:
                    job_title = full_time_job.title
            
            if job_title:
                title = "Your Proposal Was Viewed"
                body = f"Your proposal for {job_title} was viewed."
                
                send_proposal_notification(
                    db=db,
                    recipient_user_id=proposal_sender_id,
                    title=title,
                    body=body,
                    data={
                        "type": "proposal_viewed",
                        "proposal_id": str(proposal.id),
                        "job_id": str(proposal.gig_job_id or proposal.full_time_job_id),
                        "job_type": "gig" if proposal.gig_job_id else "full_time"
                    }
                )
        except Exception:
            pass
        
        # Refresh proposal to get updated is_read status
        proposal = repository.get_by_id(proposal_id)
    
    return ProposalResponse.from_orm(proposal)


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
    if gig_job['author']['id'] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view proposals for your own gig jobs"
        )
    
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_gig_job_proposals(gig_job_id, pagination)
    
    # Convert proposals to response format
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


@router.get("/full-time-job/{full_time_job_id}", response_model=ProposalListResponse)
async def get_full_time_job_proposals(
    full_time_job_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all proposals for a specific full-time job (only by the full-time job author).
    
    - **full_time_job_id**: ID of the full-time job
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    full_time_job_repository = FullTimeJobRepository(db)
    full_time_job = full_time_job_repository.get_object_by_id(full_time_job_id)
    
    if not full_time_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Full-time job not found"
        )
    
    # Check if user is the author of the full-time job
    if full_time_job.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view proposals for your own full-time jobs"
        )
    
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_full_time_job_proposals(full_time_job_id, pagination)
    
    # Convert proposals to response format
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


@router.put("/{proposal_id}")
async def update_proposal(
    proposal_id: int,
    cover_letter: Optional[str] = Form(None, min_length=10, description="Cover letter content"),
    delivery_time: Optional[int] = Form(None, ge=1, description="Delivery time in days"),
    offer_amount: Optional[float] = Form(None, ge=0, description="Offer amount in currency"),
    attachments: List[UploadFile] = File(None, description="File attachments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a proposal with file attachments (only by the author).
    
    - **proposal_id**: ID of the proposal to update
    - **cover_letter**: Updated cover letter content
    - **delivery_time**: Updated delivery time in days (optional)
    - **offer_amount**: Updated offer amount in currency (optional)
    - **attachments**: Updated file attachments (multiple files supported)
    """
    repository = ProposalRepository(db)
    attachment_repository = ProposalAttachmentRepository(db)
    
    # Get existing proposal
    existing_proposal = repository.get_by_id(proposal_id)
    if not existing_proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found"
            }
        )
    
    # Check if user has permission to update
    if existing_proposal.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "error",
                "msg": "You don't have permission to update this proposal"
            }
        )
    
    # Prepare update data
    update_data = {}
    if cover_letter is not None:
        update_data['cover_letter'] = cover_letter
    if delivery_time is not None:
        update_data['delivery_time'] = delivery_time
    if offer_amount is not None:
        update_data['offer_amount'] = offer_amount
    
    # Process file uploads if any
    if attachments:
        # Delete existing attachments
        attachment_repository.delete_by_proposal_id(proposal_id)
        
        # Save new attachments
        file_info_list = save_uploaded_files(attachments, current_user.id, proposal_id)
        for file_info in file_info_list:
            attachment_repository.create(
                proposal_id=proposal_id,
                attachment=file_info["attachment"],
                size=file_info["size"],
                name=file_info["name"]
            )
    
    # Create ProposalUpdate object
    proposal_update = ProposalUpdate(**update_data)
    
    # Update proposal
    updated_proposal = repository.update(proposal_id, proposal_update, current_user.id)
    
    if not updated_proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found or you don't have permission to update it"
            }
        )
    
    # Get the updated proposal with all relationships for response
    proposal_with_details = repository.get_by_id(proposal_id)
    
    # Determine job type for success message
    job_type = "gig job" if existing_proposal.gig_job_id else "full-time job"
    job_id = existing_proposal.gig_job_id if existing_proposal.gig_job_id else existing_proposal.full_time_job_id
    
    try:
        # Create response data with expanded job details
        response_data = ProposalResponse.from_orm(proposal_with_details)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "msg": f"Proposal successfully updated for {job_type} (ID: {job_id})",
                "data": response_data.model_dump(mode='json')
            }
        )
    except Exception as e:
        # If there's an error with the detailed response, return basic response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "msg": f"Proposal successfully updated for {job_type} (ID: {job_id})",
                "data": {
                    "id": proposal_with_details.id,
                    "user_id": proposal_with_details.user_id,
                    "gig_job_id": proposal_with_details.gig_job_id,
                    "full_time_job_id": proposal_with_details.full_time_job_id,
                    "cover_letter": proposal_with_details.cover_letter,
                    "delivery_time": proposal_with_details.delivery_time,
                    "offer_amount": proposal_with_details.offer_amount,
                    "attachments": [],
                    "created_at": proposal_with_details.created_at.isoformat() if proposal_with_details.created_at else None,
                    "updated_at": proposal_with_details.updated_at.isoformat() if proposal_with_details.updated_at else None
                }
            }
        )


@router.delete("/{proposal_id}")
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
    attachment_repository = ProposalAttachmentRepository(db)
    
    # Get existing proposal to determine job type
    existing_proposal = repository.get_by_id(proposal_id)
    if not existing_proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found"
            }
        )
    
    # Check if user has permission to delete
    if existing_proposal.user_id != current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "error",
                "msg": "You don't have permission to delete this proposal"
            }
        )
    
    # Delete attachments first
    attachment_repository.delete_by_proposal_id(proposal_id)
    
    # Delete proposal
    success = repository.delete(proposal_id, current_user.id)
    
    if not success:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found or you don't have permission to delete it"
            }
        )
    
    # Determine job type for success message
    job_type = "gig job" if existing_proposal.gig_job_id else "full-time job"
    job_id = existing_proposal.gig_job_id if existing_proposal.gig_job_id else existing_proposal.full_time_job_id
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "msg": f"Proposal successfully deleted for {job_type} (ID: {job_id})"
        }
    )


@router.get("/{proposal_id}/mark-as-read", status_code=status.HTTP_200_OK)
async def mark_proposal_as_read(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a proposal as read. Only the job owner can mark proposals as read.
    
    - **proposal_id**: ID of the proposal to mark as read
    """
    repository = ProposalRepository(db)
    proposal = repository.get_by_id(proposal_id)
    
    if not proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found"
            }
        )
    
    # Check if user is the job owner
    is_job_owner = False
    
    if proposal.gig_job_id:
        # Get gig job directly from database to ensure we have author_id
        from app.models.gig_job import GigJob
        gig_job_model = db.query(GigJob).filter(GigJob.id == proposal.gig_job_id).first()
        if gig_job_model and gig_job_model.author_id == current_user.id:
            is_job_owner = True
    elif proposal.full_time_job_id:
        full_time_job_repository = FullTimeJobRepository(db)
        full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
        if full_time_job and full_time_job.created_by_user_id == current_user.id:
            is_job_owner = True
    
    if not is_job_owner:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "error",
                "msg": "Only the job owner can mark proposals as read"
            }
        )
    
    # Check if already read
    if proposal.is_read:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "msg": "Proposal is already marked as read",
                "data": {
                    "proposal_id": proposal.id,
                    "is_read": True
                }
            }
        )
    
    # Mark as read
    updated_proposal = repository.mark_as_read(proposal_id)
    
    if not updated_proposal:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "msg": "Failed to mark proposal as read"
            }
        )
    
    # Send push notification to proposal sender (My Proposal notification)
    try:
        proposal_sender_id = proposal.user_id
        print(f"DEBUG: Proposal sender ID: {proposal_sender_id}")
        job_title = None
        
        if proposal.gig_job_id:
            gig_job_repository = GigJobRepository(db)
            gig_job = gig_job_repository.get_by_id(proposal.gig_job_id)
            if gig_job:
                job_title = gig_job.get('title', 'gig job')
                print(f"DEBUG: Gig job title: {job_title}")
        elif proposal.full_time_job_id:
            full_time_job_repository = FullTimeJobRepository(db)
            full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
            if full_time_job:
                job_title = full_time_job.title
                print(f"DEBUG: Full-time job title: {job_title}")
        
        if job_title:
            title = "Your Proposal Was Viewed"
            body = f"Your proposal for {job_title} was viewed."
            
            print(f"DEBUG: Sending notification to proposal sender (user_id={proposal_sender_id})")
            send_proposal_notification(
                db=db,
                recipient_user_id=proposal_sender_id,
                title=title,
                body=body,
                data={
                    "type": "proposal_viewed",
                    "proposal_id": str(proposal.id),
                    "job_id": str(proposal.gig_job_id or proposal.full_time_job_id),
                    "job_type": "gig" if proposal.gig_job_id else "full_time"
                }
            )
        else:
            print(f"DEBUG: Job title is None, notification not sent")
    except Exception as e:
        print(f"ERROR: Exception in mark-as-read notification: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "msg": "Proposal marked as read successfully",
            "data": {
                "proposal_id": updated_proposal.id,
                "is_read": updated_proposal.is_read
            }
        }
    )


@router.get("/mark-all-as-read", status_code=status.HTTP_200_OK)
async def mark_all_proposals_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all proposals as read for jobs owned by the current user.
    This will mark all unread proposals for both gig jobs and full-time jobs owned by the user.
    """
    repository = ProposalRepository(db)
    gig_job_repository = GigJobRepository(db)
    full_time_job_repository = FullTimeJobRepository(db)
    
    # Get all gig jobs owned by current user
    from app.models.gig_job import GigJob
    user_gig_jobs = db.query(GigJob).filter(
        GigJob.author_id == current_user.id,
        GigJob.is_deleted == False
    ).all()
    gig_job_ids = [job.id for job in user_gig_jobs]
    
    # Get all full-time jobs owned by current user
    from app.models.full_time_job import FullTimeJob
    user_full_time_jobs = db.query(FullTimeJob).filter(
        FullTimeJob.created_by_user_id == current_user.id
    ).all()
    full_time_job_ids = [job.id for job in user_full_time_jobs]
    
    # Get all unread proposals for user's jobs
    from app.models.proposal import Proposal
    from sqlalchemy import or_
    
    conditions = []
    if gig_job_ids:
        conditions.append(Proposal.gig_job_id.in_(gig_job_ids))
    if full_time_job_ids:
        conditions.append(Proposal.full_time_job_id.in_(full_time_job_ids))
    
    if not conditions:
        # User has no jobs, return empty result
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "msg": "No jobs found for this user",
                "data": {
                    "marked_count": 0,
                    "total_proposals": 0
                }
            }
        )
    
    unread_proposals = db.query(Proposal).filter(
        Proposal.is_read == False,
        Proposal.is_deleted == False,
        or_(*conditions)
    ).all()
    
    if not unread_proposals:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "msg": "No unread proposals found",
                "data": {
                    "marked_count": 0,
                    "total_proposals": 0
                }
            }
        )
    
    # Mark all proposals as read and send notifications
    marked_count = 0
    notifications_sent = 0
    
    for proposal in unread_proposals:
        try:
            # Mark as read
            updated_proposal = repository.mark_as_read(proposal.id)
            if updated_proposal:
                marked_count += 1
                
                # Send push notification to proposal sender
                try:
                    proposal_sender_id = proposal.user_id
                    job_title = None
                    
                    if proposal.gig_job_id:
                        gig_job = gig_job_repository.get_by_id(proposal.gig_job_id)
                        if gig_job:
                            job_title = gig_job.get('title', 'gig job')
                    elif proposal.full_time_job_id:
                        full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
                        if full_time_job:
                            job_title = full_time_job.title
                    
                    if job_title:
                        title = "Your Proposal Was Viewed"
                        body = f"Your proposal for {job_title} was viewed."
                        
                        send_proposal_notification(
                            db=db,
                            recipient_user_id=proposal_sender_id,
                            title=title,
                            body=body,
                            data={
                                "type": "proposal_viewed",
                                "proposal_id": str(proposal.id),
                                "job_id": str(proposal.gig_job_id or proposal.full_time_job_id),
                                "job_type": "gig" if proposal.gig_job_id else "full_time"
                            }
                        )
                        notifications_sent += 1
                except Exception:
                    pass
                    
        except Exception:
            pass
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "msg": f"Successfully marked {marked_count} proposal(s) as read",
            "data": {
                "marked_count": marked_count,
                "total_proposals": len(unread_proposals),
                "notifications_sent": notifications_sent
            }
        }
    )
