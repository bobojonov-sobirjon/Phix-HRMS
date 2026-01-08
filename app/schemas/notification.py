from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    APPLICATION = "application"
    PROPOSAL_VIEWED = "proposal_viewed"
    CHAT_MESSAGE = "chat_message"


class NotificationBase(BaseModel):
    type: NotificationType
    title: str
    body: str
    proposal_id: Optional[int] = None
    job_id: Optional[int] = None
    job_type: Optional[str] = None
    applicant_id: Optional[int] = None
    room_id: Optional[int] = None
    message_id: Optional[int] = None
    sender_id: Optional[int] = None


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    body: str
    recipient_user_id: int
    proposal_id: Optional[int] = None
    job_id: Optional[int] = None
    job_type: Optional[str] = None
    applicant_id: Optional[int] = None
    applicant_name: Optional[str] = None
    room_id: Optional[int] = None
    message_id: Optional[int] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    is_read: bool
    created_at: datetime
    proposal: Optional[dict] = Field(None, description="Full proposal details")
    recipient_user: Optional[dict] = Field(None, description="Full recipient user details")

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    page: int
    size: int
    unread_count: int = Field(default=0, description="Number of unread notifications")


class NotificationCountResponse(BaseModel):
    applications_unread: int = Field(default=0, description="Unread application notifications")
    my_proposals_unread: int = Field(default=0, description="Unread proposal viewed notifications")
    chat_messages_unread: int = Field(default=0, description="Unread chat message notifications")

