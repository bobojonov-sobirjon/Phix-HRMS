from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"
    VIDEO_CALL = "video_call"

# User Search
class UserSearchResponse(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    is_online: bool = False
    
    class Config:
        from_attributes = True

# Chat Room Schemas
class ChatRoomResponse(BaseModel):
    id: int
    name: Optional[str]
    room_type: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    other_user: Optional[Dict[str, Any]] = None  # For direct chats
    last_message: Optional[Dict[str, Any]] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True

class ChatRoomCreate(BaseModel):
    receiver_id: int = Field(..., description="ID of the user to chat with")

# Message Schemas
class ChatMessageResponse(BaseModel):
    id: int
    content: Optional[str] = None
    message_type: MessageType
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    is_read: bool
    is_deleted: bool
    is_sender: bool  # Frontend uchun: true = o'ng tomonda, false = chap tomonda
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    room_id: int
    receiver_id: int
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None

class TextMessageCreate(ChatMessageCreate):
    content: str = Field(..., min_length=1, max_length=5000)

# File Upload
class FileUploadResponse(BaseModel):
    file_name: str
    file_path: str
    file_size: int
    mime_type: str

# WebSocket Messages
class WebSocketMessage(BaseModel):
    type: str  # message, typing, presence, etc.
    data: Dict[str, Any]

class TypingIndicator(BaseModel):
    room_id: int
    user_id: int
    user_name: str
    is_typing: bool

class UserPresenceUpdate(BaseModel):
    user_id: int
    is_online: bool
    last_seen: Optional[datetime] = None

# Response Lists
class ChatRoomListResponse(BaseModel):
    rooms: List[ChatRoomResponse]
    total: int

class MessageListResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int
    has_more: bool

# Search Response
class UserSearchListResponse(BaseModel):
    users: List[UserSearchResponse]
    total: int

# Video Calling Schemas
class VideoCallTokenRequest(BaseModel):
    channel_name: str = Field(..., description="Channel name for the video call")
    uid: Optional[int] = Field(None, description="User ID (0 for auto-assign)")
    user_account: Optional[str] = Field(None, description="String-based user account")
    role: str = Field("publisher", description="Role: publisher or subscriber")
    expire_seconds: int = Field(3600, ge=60, le=86400, description="Token expiry in seconds")

class VideoCallTokenResponse(BaseModel):
    app_id: str
    channel: str
    uid: Optional[int]
    user_account: Optional[str]
    role: str
    expire_at: int
    token: str

class VideoCallRequest(BaseModel):
    receiver_id: int = Field(..., description="ID of the user to call")
    channel_name: str = Field(..., description="Channel name for the call")

class VideoCallResponse(BaseModel):
    call_id: str
    channel_name: str
    token: VideoCallTokenResponse
    receiver_id: int
    created_at: datetime

class VideoCallStatus(BaseModel):
    call_id: str
    status: str  # calling, answered, rejected, ended
    caller_id: int
    receiver_id: int
    channel_name: str
    created_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
