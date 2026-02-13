from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse
)
from app.schemas.proposal import ProposalResponse
from app.schemas.profile import UserShortDetails
from app.models.notification import NotificationType
from app.pagination import PaginationParams, create_pagination_response
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_user_id(user) -> int:
    """Get user ID from either dict or User object"""
    return user.get('id') if isinstance(user, dict) else user.id


@router.get("/applications", response_model=NotificationListResponse)
async def get_applications(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get application notifications (when someone applies to your jobs).
    
    These are notifications sent to job owners when someone submits a proposal
    for their gig job or full-time job.
    """
    repository = NotificationRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    notifications, total = repository.get_applications(
        user_id=get_user_id(current_user),
        pagination=pagination
    )
    
    unread_count = repository.get_unread_count(
        user_id=get_user_id(current_user),
        notification_type=NotificationType.PROPOSAL_RECEIVED
    )
    
    notification_responses = []
    for notification in notifications:
        applicant_name = None
        if notification.applicant:
            applicant_name = notification.applicant.name
        
        proposal_details = None
        if notification.proposal:
            proposal_details = ProposalResponse.from_orm(notification.proposal).model_dump()
        
        recipient_user_details = None
        if notification.recipient:
            user_data = UserShortDetails.model_validate(notification.recipient).model_dump()
            if user_data.get("avatar_url") and not user_data["avatar_url"].startswith(('http://', 'https://')):
                user_data["avatar_url"] = f"{settings.BASE_URL}{user_data['avatar_url']}"
            recipient_user_details = user_data
        
        notification_responses.append(NotificationResponse(
            id=notification.id,
            type=notification.type.value,
            title=notification.title,
            body=notification.body,
            recipient_user_id=notification.recipient_user_id,
            proposal_id=notification.proposal_id,
            job_id=notification.job_id,
            job_type=notification.job_type,
            applicant_id=notification.applicant_id,
            applicant_name=applicant_name,
            is_read=notification.is_read,
            created_at=notification.created_at,
            proposal=proposal_details,
            recipient_user=recipient_user_details
        ))
    
    return NotificationListResponse(
        notifications=notification_responses,
        total=total,
        page=page,
        size=size,
        unread_count=unread_count
    )


@router.get("/my-proposals", response_model=NotificationListResponse)
async def get_my_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get "My Proposal" notifications (when your proposals are viewed).
    
    These are notifications sent to proposal senders when a job owner
    views their proposal.
    """
    repository = NotificationRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    notifications, total = repository.get_my_proposals(
        user_id=get_user_id(current_user),
        pagination=pagination
    )
    
    unread_count = repository.get_unread_count(
        user_id=get_user_id(current_user),
        notification_type=NotificationType.PROPOSAL_ACCEPTED
    )
    
    notification_responses = []
    for notification in notifications:
        proposal_details = None
        if notification.proposal:
            proposal_details = ProposalResponse.from_orm(notification.proposal).model_dump()
        
        recipient_user_details = None
        if notification.recipient:
            user_data = UserShortDetails.model_validate(notification.recipient).model_dump()
            if user_data.get("avatar_url") and not user_data["avatar_url"].startswith(('http://', 'https://')):
                user_data["avatar_url"] = f"{settings.BASE_URL}{user_data['avatar_url']}"
            recipient_user_details = user_data
        
        notification_responses.append(NotificationResponse(
            id=notification.id,
            type=notification.type.value,
            title=notification.title,
            body=notification.body,
            recipient_user_id=notification.recipient_user_id,
            proposal_id=notification.proposal_id,
            job_id=notification.job_id,
            job_type=notification.job_type,
            applicant_id=notification.applicant_id,
            applicant_name=None,
            is_read=notification.is_read,
            created_at=notification.created_at,
            proposal=proposal_details,
            recipient_user=recipient_user_details
        ))
    
    return NotificationListResponse(
        notifications=notification_responses,
        total=total,
        page=page,
        size=size,
        unread_count=unread_count
    )


@router.get("/counts", response_model=NotificationCountResponse)
async def get_notification_counts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notification counts for Applications and My Proposals"""
    repository = NotificationRepository(db)
    
    applications_unread = repository.get_unread_count(
        user_id=get_user_id(current_user),
        notification_type=NotificationType.APPLICATION
    )
    
    my_proposals_unread = repository.get_unread_count(
        user_id=get_user_id(current_user),
        notification_type=NotificationType.PROPOSAL_ACCEPTED
    )
    
    chat_messages_unread = repository.get_unread_count(
        user_id=get_user_id(current_user),
        notification_type=NotificationType.MESSAGE_RECEIVED
    )
    
    return NotificationCountResponse(
        applications_unread=applications_unread,
        my_proposals_unread=my_proposals_unread,
        chat_messages_unread=chat_messages_unread
    )


@router.get("/chat-messages", response_model=NotificationListResponse)
async def get_chat_messages(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat message notifications (when someone sends you a chat message).
    
    These are notifications sent to users when they receive chat messages.
    """
    repository = NotificationRepository(db)
    pagination = PaginationParams(page=page, size=size)
    
    notifications, total = repository.get_chat_messages(
        user_id=get_user_id(current_user),
        pagination=pagination
    )
    
    unread_count = repository.get_unread_count(
        user_id=get_user_id(current_user),
        notification_type=NotificationType.MESSAGE_RECEIVED
    )
    
    notification_responses = []
    for notification in notifications:
        sender_name = None
        if notification.sender:
            sender_name = notification.sender.name
        
        recipient_user_details = None
        if notification.recipient:
            user_data = UserShortDetails.model_validate(notification.recipient).model_dump()
            if user_data.get("avatar_url") and not user_data["avatar_url"].startswith(('http://', 'https://')):
                user_data["avatar_url"] = f"{settings.BASE_URL}{user_data['avatar_url']}"
            recipient_user_details = user_data
        
        notification_responses.append(NotificationResponse(
            id=notification.id,
            type=notification.type.value,
            title=notification.title,
            body=notification.body,
            recipient_user_id=notification.recipient_user_id,
            proposal_id=notification.proposal_id,
            job_id=notification.job_id,
            job_type=notification.job_type,
            applicant_id=notification.applicant_id,
            applicant_name=None,
            room_id=notification.room_id,
            message_id=notification.message_id,
            sender_id=notification.sender_id,
            sender_name=sender_name,
            is_read=notification.is_read,
            created_at=notification.created_at,
            proposal=None,
            recipient_user=recipient_user_details
        ))
    
    return NotificationListResponse(
        notifications=notification_responses,
        total=total,
        page=page,
        size=size,
        unread_count=unread_count
    )


@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    repository = NotificationRepository(db)
    success = repository.mark_as_read(notification_id, get_user_id(current_user))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}
