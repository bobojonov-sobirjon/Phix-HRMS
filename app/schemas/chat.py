from pydantic import BaseModel, Field
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
    receiver_id: int = Field(..., description="ID of the user to chat with")

# Sender Details Schema
class SenderDetails(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    is_online: bool = False
    
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
    sender_details: Optional[SenderDetails] = None
    
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
    total: int
    has_more: bool

# Search Response
class UserSearchListResponse(BaseModel):
    users: List[UserSearchResponse]
    total: int

