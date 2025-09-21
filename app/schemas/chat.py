from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"

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
    room_id: int
    sender_id: int
    receiver_id: int
    sender_name: str
    receiver_name: str
    sender_avatar: Optional[str] = None
    receiver_avatar: Optional[str] = None
    message_type: MessageType
    content: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    is_read: bool
    is_deleted: bool
    
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
