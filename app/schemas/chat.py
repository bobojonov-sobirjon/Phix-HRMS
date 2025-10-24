from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"

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
    receiver_id: int = Field(..., gt=0, description="ID of the user to chat with")
    
    @validator('receiver_id')
    def validate_receiver_id(cls, v):
        if v <= 0:
            raise ValueError('Receiver ID must be a positive integer')
        return v

# Sender Details Schema
class SenderDetails(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    is_online: bool = False
    
    class Config:
        from_attributes = True

# Receiver Details Schema
class ReceiverDetails(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    is_online: bool = False
    
    class Config:
        from_attributes = True

# Online User Details Schema
class OnlineUserDetails(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    is_verified: bool = False
    last_seen: datetime
    is_online: bool = True
    
    class Config:
        from_attributes = True

# Online Users Response Schema
class OnlineUsersResponse(BaseModel):
    online_users: List[OnlineUserDetails]
    
    class Config:
        from_attributes = True

# File Schema for multiple files
class FileData(BaseModel):
    file_name: str
    file_path: str
    file_size: int
    mime_type: str

# Message Schemas
class ChatMessageResponse(BaseModel):
    id: int
    content: Optional[str] = None
    message_type: MessageType
    file_name: Optional[str] = None  # For backward compatibility
    file_path: Optional[str] = None  # For backward compatibility
    file_size: Optional[int] = None  # For backward compatibility
    files_data: Optional[List[FileData]] = None  # For multiple files
    created_at: datetime
    is_read: bool
    is_deleted: bool
    is_sender: bool  # Frontend uchun: true = o'ng tomonda, false = chap tomonda
    is_liked: bool = False  # Whether current user liked this message
    like_count: int = 0  # Total number of likes for this message
    sender_details: Optional[SenderDetails] = None
    receiver_details: Optional[ReceiverDetails] = None
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    room_id: int
    receiver_id: int
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None

class TextMessageCreate(ChatMessageCreate):
    content: str = Field(..., min_length=1, max_length=5000)

# File Upload schemas removed - using WebSocket only for file uploads

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
    total: int  # Total number of messages in the room
    has_more: bool  # Whether there are more pages available
    page: int = 1  # Current page number
    per_page: int = 50  # Number of messages per page
    total_pages: int = 1  # Total number of pages

# Search Response
class UserSearchListResponse(BaseModel):
    users: List[UserSearchResponse]
    total: int

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

# Message Like Schemas
class MessageLikeRequest(BaseModel):
    message_id: int = Field(..., description="ID of the message to like/unlike")

class MessageLikeResponse(BaseModel):
    action: str  # "liked" or "unliked"
    like_count: int
    message_id: int

# Room Check Response
class RoomCheckResponse(BaseModel):
    status: str
    msg: str
    data: List[ChatRoomResponse]