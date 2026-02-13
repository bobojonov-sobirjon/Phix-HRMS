from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.auth import get_current_user
from app.utils.decorators import handle_errors
from app.utils.permissions import is_admin_user
from app.utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    forbidden_error,
    validate_entity_exists
)
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


def get_user_id(user) -> int:
    """Get user ID from either dict or User object"""
    return user.get('id') if isinstance(user, dict) else user.id

UPLOAD_DIR = "static/proposals"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=ProposalListResponse)
@handle_errors
async def get_all_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all proposals (admin only).
    
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10, max: 100)
    """
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can view all proposals")
    
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_all_proposals(pagination)
    
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


def get_user_device_tokens(db: Session, user_id: int) -> List[str]:
    """Get all active device tokens for a user"""
    from sqlalchemy import text
    try:
        result = db.execute(text("""
            SELECT device_token 
            FROM user_device_tokens 
            WHERE user_id = :user_id 
            AND is_active = true
            AND LOWER(device_type::text) IN ('ios', 'android')
        """), {"user_id": user_id})
        return [row[0] for row in result if row[0]]
    except Exception as e:
        print(f"DEBUG: Error getting device tokens: {str(e)}")
        try:
            device_tokens = db.query(UserDeviceToken).filter(
                UserDeviceToken.user_id == user_id,
                UserDeviceToken.is_active == True
            ).all()
            valid_tokens = []
            for token in device_tokens:
                try:
                    if token.device_token:
                        valid_tokens.append(token.device_token)
                except (LookupError, KeyError, ValueError):
                    continue
            return valid_tokens
        except Exception:
            return []


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
            try:
                result = send_push_notification_multiple(
                    device_tokens=device_tokens,
                    title=title,
                    body=body,
                    data={str(k): str(v) for k, v in data.items()}
                )
                skipped = result.get('skipped_count', 0)
                if skipped > 0:
                    print(f"DEBUG: Notification result - Success: {result.get('success_count', 0)}, Failed: {result.get('failure_count', 0)}, Skipped: {skipped}")
                else:
                    print(f"DEBUG: Notification result - Success: {result.get('success_count', 0)}, Failed: {result.get('failure_count', 0)}")
            except FileNotFoundError as fe:
                print(f"WARNING: Firebase service account file not found. Push notification skipped, but notification is saved to database: {str(fe)}")
            except Exception as fe:
                print(f"WARNING: Failed to send push notification (notification saved to database): {str(fe)}")
        else:
            print(f"DEBUG: No device tokens found for user_id={recipient_user_id}")
    except Exception as e:
        print(f"WARNING: Failed to send notification to user_id={recipient_user_id}: {str(e)}")
        if "Firebase service account file not found" not in str(e):
            import traceback
            traceback.print_exc()


def save_uploaded_files(files: List[UploadFile], user_id: int, proposal_id: int) -> List[dict]:
    """Save uploaded files and return list of file info"""
    file_info_list = []
    
    for file in files:
        if file.filename:
            user_dir = os.path.join(UPLOAD_DIR, f"user_{user_id}")
            os.makedirs(user_dir, exist_ok=True)
            
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"proposal_{proposal_id}_{file.filename}"
            file_path = os.path.join(user_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            relative_path = os.path.join("proposals", f"user_{user_id}", unique_filename)
            
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
    # Filter out invalid IDs (0 or negative)
    if gig_job_id is not None and gig_job_id <= 0:
        gig_job_id = None
    if full_time_job_id is not None and full_time_job_id <= 0:
        full_time_job_id = None
    
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
        
        if gig_job['author']['id'] == get_user_id(current_user):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "msg": "You cannot submit a proposal to your own gig job"
                }
            )
        
        if repository.check_user_proposal_exists(get_user_id(current_user), gig_job_id, "gig"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "msg": "You have already submitted a proposal for this gig job"
                }
            )
    
    elif full_time_job_id:
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
        
        if repository.check_user_proposal_exists(get_user_id(current_user), full_time_job_id, "full_time"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "msg": "You have already submitted a proposal for this full-time job"
                }
            )
    
    proposal_data = ProposalCreate(
        cover_letter=cover_letter,
        delivery_time=delivery_time,
        offer_amount=offer_amount,
        gig_job_id=gig_job_id,
        full_time_job_id=full_time_job_id
    )
    
    user_id = get_user_id(current_user)
    proposal = repository.create(proposal_data, user_id)
    
    if attachments:
        file_info_list = save_uploaded_files(attachments, user_id, proposal.id)
        for file_info in file_info_list:
            attachment_repository.create(
                proposal_id=proposal.id,
                attachment=file_info["attachment"],
                size=file_info["size"],
                name=file_info["name"]
            )
    
    proposal_with_details = repository.get_by_id(proposal.id)
    
    job_type = "gig job" if gig_job_id else "full-time job"
    job_id = gig_job_id if gig_job_id else full_time_job_id
    
    try:
        print(f"DEBUG: Starting notification process for proposal {proposal.id}")
        job_owner_id = None
        job_title = None
        
        if gig_job_id:
            from app.models.gig_job import GigJob
            gig_job_model = db.query(GigJob).filter(GigJob.id == gig_job_id).first()
            print(f"DEBUG: Gig job model found: {gig_job_model is not None}")
            if gig_job_model:
                job_owner_id = gig_job_model.author_id
                job_title = gig_job_model.title
                print(f"DEBUG: Gig job owner_id={job_owner_id}, title={job_title}")
        elif full_time_job_id:
            full_time_job_repository = FullTimeJobRepository(db)
            full_time_job = full_time_job_repository.get_object_by_id(full_time_job_id)
            print(f"DEBUG: Full-time job found: {full_time_job is not None}")
            if full_time_job:
                job_owner_id = full_time_job.created_by_user_id
                job_title = full_time_job.title
                print(f"DEBUG: Full-time job owner_id={job_owner_id}, title={job_title}")
        
        print(f"DEBUG: Job owner ID: {job_owner_id}, Current user ID: {user_id}")
        
        if job_owner_id and job_owner_id != user_id:
            applicant_name = current_user.name or current_user.email or "Someone"
            position_name = job_title or "position"
            
            title = "New Application Received"
            body = f"{applicant_name} applied for {position_name} position"
            
            print(f"DEBUG: Sending notification to job owner (user_id={job_owner_id})")
            print(f"DEBUG: Notification title: {title}, body: {body}")
            
            from app.repositories.notification_repository import NotificationRepository
            from app.models.notification import NotificationType
            from app.utils.websocket_manager import manager
            notification_repo = NotificationRepository(db)
            notification = notification_repo.create(
                type=NotificationType.PROPOSAL_RECEIVED,
                title=title,
                body=body,
                recipient_user_id=job_owner_id,
                proposal_id=proposal.id,
                job_id=job_id,
                job_type="gig" if gig_job_id else "full_time",
                applicant_id=user_id
            )
            
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
                    "applicant_id": str(user_id)
                }
            )
            print(f"DEBUG: Notification sent successfully")
        else:
            print(f"DEBUG: Notification not sent - job_owner_id={job_owner_id}, get_user_id(current_user)={user_id}")
    except Exception as e:
        print(f"ERROR: Exception in proposal creation notification: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
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
    
    proposals, total = repository.get_user_gig_job_proposals(get_user_id(current_user), pagination)
    
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
    
    proposals, total = repository.get_user_full_time_job_proposals(get_user_id(current_user), pagination)
    
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


@router.get("/{proposal_id}", response_model=ProposalResponse)
@handle_errors
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
    validate_entity_exists(proposal, "Proposal")
    
    is_job_owner = False
    if proposal.user_id != get_user_id(current_user):
        has_permission = False
        
        if proposal.gig_job_id:
            gig_job_repository = GigJobRepository(db)
            gig_job = gig_job_repository.get_by_id(proposal.gig_job_id)
            if gig_job and gig_job['author']['id'] == get_user_id(current_user):
                has_permission = True
                is_job_owner = True
        elif proposal.full_time_job_id:
            full_time_job_repository = FullTimeJobRepository(db)
            full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
            if full_time_job and full_time_job.created_by_user_id == get_user_id(current_user):
                has_permission = True
                is_job_owner = True
        
        if not has_permission:
            raise forbidden_error("You don't have permission to view this proposal")
    
    if is_job_owner and not proposal.is_read:
        repository.mark_as_read(proposal_id)
        
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
                
                from app.repositories.notification_repository import NotificationRepository
                from app.models.notification import NotificationType
                notification_repo = NotificationRepository(db)
                notification_repo.create(
                    type=NotificationType.PROPOSAL_ACCEPTED,
                    title=title,
                    body=body,
                    recipient_user_id=proposal_sender_id,
                    proposal_id=proposal.id,
                    job_id=proposal.gig_job_id or proposal.full_time_job_id,
                    job_type="gig" if proposal.gig_job_id else "full_time"
                )
                
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
        
        proposal = repository.get_by_id(proposal_id)
    
    return ProposalResponse.from_orm(proposal)


@router.get("/gig-job/{gig_job_id}", response_model=ProposalListResponse)
@handle_errors
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
    validate_entity_exists(gig_job, "Gig job")
    
    if gig_job['author']['id'] != get_user_id(current_user):
        raise forbidden_error("You can only view proposals for your own gig jobs")
    
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_gig_job_proposals(gig_job_id, pagination)
    
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


@router.get("/full-time-job/{full_time_job_id}", response_model=ProposalListResponse)
@handle_errors
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
    validate_entity_exists(full_time_job, "Full-time job")
    
    if full_time_job.created_by_user_id != get_user_id(current_user):
        raise forbidden_error("You can only view proposals for your own full-time jobs")
    
    repository = ProposalRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    proposals, total = repository.get_full_time_job_proposals(full_time_job_id, pagination)
    
    proposal_responses = [ProposalResponse.from_orm(proposal) for proposal in proposals]
    
    return create_pagination_response(
        items=proposal_responses,
        total=total,
        pagination=pagination
    )


@router.put("/{proposal_id}")
@handle_errors
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
    
    existing_proposal = repository.get_by_id(proposal_id)
    validate_entity_exists(existing_proposal, "Proposal")
    
    if existing_proposal.user_id != get_user_id(current_user):
        raise forbidden_error("You don't have permission to update this proposal")
    
    update_data = {}
    if cover_letter is not None:
        update_data['cover_letter'] = cover_letter
    if delivery_time is not None:
        update_data['delivery_time'] = delivery_time
    if offer_amount is not None:
        update_data['offer_amount'] = offer_amount
    
    if attachments:
        attachment_repository.delete_by_proposal_id(proposal_id)
        
        file_info_list = save_uploaded_files(attachments, get_user_id(current_user), proposal_id)
        for file_info in file_info_list:
            attachment_repository.create(
                proposal_id=proposal_id,
                attachment=file_info["attachment"],
                size=file_info["size"],
                name=file_info["name"]
            )
    
    proposal_update = ProposalUpdate(**update_data)
    
    updated_proposal = repository.update(proposal_id, proposal_update, get_user_id(current_user))
    
    if not updated_proposal:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found or you don't have permission to update it"
            }
        )
    
    proposal_with_details = repository.get_by_id(proposal_id)
    
    job_type = "gig job" if existing_proposal.gig_job_id else "full-time job"
    job_id = existing_proposal.gig_job_id if existing_proposal.gig_job_id else existing_proposal.full_time_job_id
    
    try:
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
@handle_errors
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
    
    existing_proposal = repository.get_by_id(proposal_id)
    validate_entity_exists(existing_proposal, "Proposal")
    
    if existing_proposal.user_id != get_user_id(current_user):
        raise forbidden_error("You don't have permission to delete this proposal")
    
    attachment_repository.delete_by_proposal_id(proposal_id)
    
    success = repository.delete(proposal_id, get_user_id(current_user))
    
    if not success:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "msg": "Proposal not found or you don't have permission to delete it"
            }
        )
    
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
    
    is_job_owner = False
    
    if proposal.gig_job_id:
        from app.models.gig_job import GigJob
        gig_job_model = db.query(GigJob).filter(GigJob.id == proposal.gig_job_id).first()
        if gig_job_model and gig_job_model.author_id == get_user_id(current_user):
            is_job_owner = True
    elif proposal.full_time_job_id:
        full_time_job_repository = FullTimeJobRepository(db)
        full_time_job = full_time_job_repository.get_object_by_id(proposal.full_time_job_id)
        if full_time_job and full_time_job.created_by_user_id == get_user_id(current_user):
            is_job_owner = True
    
    if not is_job_owner:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "error",
                "msg": "Only the job owner can mark proposals as read"
            }
        )
    
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
    
    updated_proposal = repository.mark_as_read(proposal_id)
    
    if not updated_proposal:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "msg": "Failed to mark proposal as read"
            }
        )
    
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
            
            from app.repositories.notification_repository import NotificationRepository
            from app.models.notification import NotificationType
            notification_repo = NotificationRepository(db)
            notification_repo.create(
                type=NotificationType.PROPOSAL_ACCEPTED,
                title=title,
                body=body,
                recipient_user_id=proposal_sender_id,
                proposal_id=proposal.id,
                job_id=proposal.gig_job_id or proposal.full_time_job_id,
                job_type="gig" if proposal.gig_job_id else "full_time"
            )
            
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
    
    from app.models.gig_job import GigJob
    user_gig_jobs = db.query(GigJob).filter(
        GigJob.author_id == get_user_id(current_user),
        GigJob.is_deleted == False
    ).all()
    gig_job_ids = [job.id for job in user_gig_jobs]
    
    from app.models.full_time_job import FullTimeJob
    user_full_time_jobs = db.query(FullTimeJob).filter(
        FullTimeJob.created_by_user_id == get_user_id(current_user)
    ).all()
    full_time_job_ids = [job.id for job in user_full_time_jobs]
    
    from app.models.proposal import Proposal
    from sqlalchemy import or_
    
    conditions = []
    if gig_job_ids:
        conditions.append(Proposal.gig_job_id.in_(gig_job_ids))
    if full_time_job_ids:
        conditions.append(Proposal.full_time_job_id.in_(full_time_job_ids))
    
    if not conditions:
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
    
    marked_count = 0
    notifications_sent = 0
    
    for proposal in unread_proposals:
        try:
            updated_proposal = repository.mark_as_read(proposal.id)
            if updated_proposal:
                marked_count += 1
                
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
                        
                        from app.repositories.notification_repository import NotificationRepository
                        from app.models.notification import NotificationType
                        notification_repo = NotificationRepository(db)
                        notification_repo.create(
                            type=NotificationType.PROPOSAL_ACCEPTED,
                            title=title,
                            body=body,
                            recipient_user_id=proposal_sender_id,
                            proposal_id=proposal.id,
                            job_id=proposal.gig_job_id or proposal.full_time_job_id,
                            job_type="gig" if proposal.gig_job_id else "full_time"
                        )
                        
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
