from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ..database import get_db
from ..repositories.chat_repository import ChatRepository
from ..schemas.chat import (
    UserSearchResponse, UserSearchListResponse,
    ChatRoomResponse, ChatRoomCreate, ChatRoomListResponse,
    ChatMessageResponse, ChatMessageCreate, TextMessageCreate, MessageListResponse,
    WebSocketMessage, TypingIndicator, UserPresenceUpdate,
    VideoCallTokenRequest, VideoCallTokenResponse, VideoCallRequest, VideoCallResponse, VideoCallStatus,
    MessageLikeRequest, MessageLikeResponse, RoomCheckResponse,
    OnlineUsersResponse, OnlineUserDetails
)
from ..utils.websocket_manager import manager
from ..utils.file_upload import file_upload_manager
from ..utils.auth import get_current_user
from ..utils.agora_tokens import generate_rtc_token
from ..models.user import User
import uuid

router = APIRouter(tags=["Chat"])

# User Search Endpoints
@router.get("/search-users", response_model=UserSearchListResponse)
async def search_users(
    email: str = Query(..., min_length=1, description="Email to search for"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search users by email"""
    chat_repo = ChatRepository(db)
    users = chat_repo.search_users_by_email(email, current_user.id, limit)
    
    user_responses = []
    for user in users:
        is_online = chat_repo.is_user_online(user.id)
        user_responses.append(UserSearchResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            is_online=is_online
        ))
    
    return UserSearchListResponse(
        users=user_responses,
        total=len(user_responses)
    )

# Chat Room Endpoints
@router.post("/rooms", response_model=ChatRoomResponse)
async def create_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a direct chat room with another user"""
    chat_repo = ChatRepository(db)
    
    # Validate receiver_id
    if room_data.receiver_id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot create a room with yourself"
        )
    
    # Check if receiver exists and is active
    receiver = db.query(User).filter(
        User.id == room_data.receiver_id,
        User.is_active == True
    ).first()
    if not receiver:
        raise HTTPException(
            status_code=404, 
            detail="User not found or inactive"
        )
    
    # Check if room already exists between these users
    existing_room = chat_repo.get_direct_room(current_user.id, room_data.receiver_id)
    if existing_room:
        # Return existing room instead of creating new one
        other_user = chat_repo.get_room_other_user(existing_room.id, current_user.id)
        other_user_info = None
        if other_user:
            is_online = chat_repo.is_user_online(other_user.id)
            other_user_info = {
                "id": other_user.id,
                "name": other_user.name,
                "email": other_user.email,
                "avatar_url": other_user.avatar_url,
                "is_online": is_online
            }
        
        # Get last message
        last_message = chat_repo.get_last_message(existing_room.id)
        last_message_info = None
        if last_message:
            last_message_info = {
                "id": last_message.id,
                "content": last_message.content,
                "message_type": last_message.message_type,
                "created_at": last_message.created_at,
                "sender_name": last_message.sender.name
            }
        
        # Get unread count
        unread_counts = chat_repo.get_unread_count(current_user.id)
        unread_count = unread_counts.get(existing_room.id, 0)
        
        return ChatRoomResponse(
            id=existing_room.id,
            name=existing_room.name,
            room_type=existing_room.room_type,
            created_by=existing_room.created_by,
            created_at=existing_room.created_at,
            updated_at=existing_room.updated_at,
            is_active=existing_room.is_active,
            other_user=other_user_info,
            last_message=last_message_info,
            unread_count=unread_count
        )
    
    # Create new room
    try:
        room = chat_repo.create_direct_room(current_user.id, room_data.receiver_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create room: {str(e)}"
        )
    
    # Get other user info
    other_user = chat_repo.get_room_other_user(room.id, current_user.id)
    other_user_info = None
    if other_user:
        is_online = chat_repo.is_user_online(other_user.id)
        other_user_info = {
            "id": other_user.id,
            "name": other_user.name,
            "email": other_user.email,
            "avatar_url": other_user.avatar_url,
            "is_online": is_online
        }
    
    # Get last message (should be None for new room)
    last_message = chat_repo.get_last_message(room.id)
    last_message_info = None
    if last_message:
        last_message_info = {
            "id": last_message.id,
            "content": last_message.content,
            "message_type": last_message.message_type,
            "created_at": last_message.created_at,
            "sender_name": last_message.sender.name
        }
    
    # Get unread count (should be 0 for new room)
    unread_counts = chat_repo.get_unread_count(current_user.id)
    unread_count = unread_counts.get(room.id, 0)
    
    return ChatRoomResponse(
        id=room.id,
        name=room.name,
        room_type=room.room_type,
        created_by=room.created_by,
        created_at=room.created_at,
        updated_at=room.updated_at,
        is_active=room.is_active,
        other_user=other_user_info,
        last_message=last_message_info,
        unread_count=unread_count
    )

@router.get("/rooms", response_model=ChatRoomListResponse)
async def get_user_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all rooms for the current user"""
    chat_repo = ChatRepository(db)
    rooms = chat_repo.get_user_rooms(current_user.id)
    
    # Get unread counts
    unread_counts = chat_repo.get_unread_count(current_user.id)
    
    room_responses = []
    for room in rooms:
        # Get other user info
        other_user = chat_repo.get_room_other_user(room.id, current_user.id)
        other_user_info = None
        if other_user:
            is_online = chat_repo.is_user_online(other_user.id)
            other_user_info = {
                "id": other_user.id,
                "name": other_user.name,
                "email": other_user.email,
                "avatar_url": other_user.avatar_url,
                "is_online": is_online
            }
        
        # Get last message
        last_message = chat_repo.get_last_message(room.id)
        last_message_info = None
        if last_message:
            last_message_info = {
                "id": last_message.id,
                "content": last_message.content,
                "message_type": last_message.message_type,
                "created_at": last_message.created_at,
                "sender_name": last_message.sender.name
            }
        
        unread_count = unread_counts.get(room.id, 0)
        
        room_responses.append(ChatRoomResponse(
            id=room.id,
            name=room.name,
            room_type=room.room_type,
            created_by=room.created_by,
            created_at=room.created_at,
            updated_at=room.updated_at,
            is_active=room.is_active,
            other_user=other_user_info,
            last_message=last_message_info,
            unread_count=unread_count
        ))
    
    return ChatRoomListResponse(
        rooms=room_responses,
        total=len(room_responses)
    )

@router.get("/rooms/{room_id}")
async def get_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific room with all messages"""
    chat_repo = ChatRepository(db)
    room = chat_repo.get_room(room_id, current_user.id)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Get other user info
    other_user = chat_repo.get_room_other_user(room.id, current_user.id)
    other_user_info = None
    if other_user:
        is_online = chat_repo.is_user_online(other_user.id)
        other_user_info = {
            "id": other_user.id,
            "name": other_user.name,
            "email": other_user.email,
            "avatar_url": other_user.avatar_url,
            "is_online": is_online
        }
    
    # Get last message
    last_message = chat_repo.get_last_message(room.id)
    last_message_info = None
    if last_message:
        last_message_info = {
            "id": last_message.id,
            "content": last_message.content,
            "message_type": last_message.message_type,
            "created_at": last_message.created_at,
            "sender_name": last_message.sender.name
        }
    
    # Get unread count
    unread_counts = chat_repo.get_unread_count(current_user.id)
    unread_count = unread_counts.get(room.id, 0)
    
    # Get all messages for this room
    messages = chat_repo.get_room_messages(room_id, current_user.id, page=1, per_page=1000)  # Get all messages
    
    message_responses = []
    for message in messages:
        # Determine if current user is sender (for frontend positioning)
        is_sender = message.sender_id == current_user.id
        
        # Check if current user liked this message
        is_liked = chat_repo.is_message_liked_by_user(message.id, current_user.id)
        like_count = chat_repo.get_message_like_count(message.id)
        
        # Build full URLs for files
        file_url = None
        files_data_with_urls = None
        
        if message.file_path:
            from ..config import settings
            # Replace backslashes with forward slashes for web URLs
            clean_path = message.file_path.replace("\\", "/")
            file_url = f"{settings.BASE_URL}/{clean_path}"
        
        if message.files_data:
            from ..config import settings
            files_data_with_urls = []
            for file_data in message.files_data:
                clean_path = file_data["file_path"].replace("\\", "/")
                file_data_with_url = {
                    "file_name": file_data["file_name"],
                    "file_path": f"{settings.BASE_URL}/{clean_path}",
                    "file_size": file_data["file_size"],
                    "mime_type": file_data["mime_type"]
                }
                files_data_with_urls.append(file_data_with_url)
        
        # Get sender details
        sender_details = None
        if message.sender:
            is_online = chat_repo.is_user_online(message.sender.id)
            sender_details = {
                "id": message.sender.id,
                "name": message.sender.name,
                "email": message.sender.email,
                "avatar_url": message.sender.avatar_url,
                "is_online": is_online
            }
        
        # Get receiver details
        receiver_details = None
        if message.receiver:
            is_online = chat_repo.is_user_online(message.receiver.id)
            receiver_details = {
                "id": message.receiver.id,
                "name": message.receiver.name,
                "email": message.receiver.email,
                "avatar_url": message.receiver.avatar_url,
                "is_online": is_online
            }
        
        # Create message response based on message type
        message_response = {
            "id": message.id,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
            "is_read": message.is_read,
            "is_deleted": message.is_deleted,
            "is_sender": is_sender,  # Frontend uchun: true = o'ng tomonda, false = chap tomonda
            "is_liked": is_liked,
            "like_count": like_count,
            "sender_details": sender_details,
            "receiver_details": receiver_details
        }
        
        # Add file-related fields only if they exist
        if message.file_name:
            message_response["file_name"] = message.file_name
        if file_url:
            message_response["file_path"] = file_url
        if message.file_size:
            message_response["file_size"] = message.file_size
        if files_data_with_urls:
            message_response["files_data"] = files_data_with_urls
            
        message_responses.append(message_response)
    
    return {
        "id": room.id,
        "name": room.name,
        "room_type": room.room_type,
        "created_by": room.created_by,
        "created_at": room.created_at,
        "updated_at": room.updated_at,
        "is_active": room.is_active,
        "other_user": other_user_info,
        "last_message": last_message_info,
        "unread_count": unread_count,
        "message_list": {
            "messages": message_responses,
            "total": len(message_responses)
        }
    }

# Message Endpoints - All messages are sent via WebSocket for real-time delivery

@router.get("/rooms/{room_id}/messages", response_model=MessageListResponse)
async def get_room_messages(
    room_id: int,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    per_page: int = Query(50, ge=1, le=100, description="Number of messages per page (max 100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a room with pagination"""
    chat_repo = ChatRepository(db)
    
    # Verify user has access to the room
    room = chat_repo.get_room(room_id, current_user.id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Get total count of messages in the room
    total_count = chat_repo.get_room_messages_count(room_id, current_user.id)
    
    # Get paginated messages
    messages = chat_repo.get_room_messages(room_id, current_user.id, page, per_page)
    
    message_responses = []
    for message in messages:
        # Determine if current user is sender (for frontend positioning)
        is_sender = message.sender_id == current_user.id
        
        # Check if current user liked this message
        is_liked = chat_repo.is_message_liked_by_user(message.id, current_user.id)
        like_count = chat_repo.get_message_like_count(message.id)
        
        # Build full URLs for files
        file_url = None
        files_data_with_urls = None
        
        if message.file_path:
            from ..config import settings
            # Replace backslashes with forward slashes for web URLs
            clean_path = message.file_path.replace("\\", "/")
            file_url = f"{settings.BASE_URL}/{clean_path}"
        
        if message.files_data:
            from ..config import settings
            files_data_with_urls = []
            for file_data in message.files_data:
                clean_path = file_data["file_path"].replace("\\", "/")
                file_data_with_url = {
                    "file_name": file_data["file_name"],
                    "file_path": f"{settings.BASE_URL}/{clean_path}",
                    "file_size": file_data["file_size"],
                    "mime_type": file_data["mime_type"]
                }
                files_data_with_urls.append(file_data_with_url)
        
        # Get sender details
        sender_details = None
        if message.sender:
            is_online = chat_repo.is_user_online(message.sender.id)
            sender_details = {
                "id": message.sender.id,
                "name": message.sender.name,
                "email": message.sender.email,
                "avatar_url": message.sender.avatar_url,
                "is_online": is_online
            }
        
        # Get receiver details
        receiver_details = None
        if message.receiver:
            is_online = chat_repo.is_user_online(message.receiver.id)
            receiver_details = {
                "id": message.receiver.id,
                "name": message.receiver.name,
                "email": message.receiver.email,
                "avatar_url": message.receiver.avatar_url,
                "is_online": is_online
            }
        
        # Create message data based on message type
        message_data = {
            "id": message.id,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at,
            "is_read": message.is_read,
            "is_deleted": message.is_deleted,
            "is_sender": is_sender,
            "is_liked": is_liked,
            "like_count": like_count,
            "sender_details": sender_details,
            "receiver_details": receiver_details
        }
        
        # Add file-related fields only if they exist
        if message.file_name:
            message_data["file_name"] = message.file_name
        if file_url:
            message_data["file_path"] = file_url
        if message.file_size:
            message_data["file_size"] = message.file_size
        if files_data_with_urls:
            message_data["files_data"] = files_data_with_urls
            
        message_responses.append(ChatMessageResponse(**message_data))
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
    has_more = page < total_pages
    
    return MessageListResponse(
        messages=message_responses,
        total=total_count,  # Total count of all messages in the room
        has_more=has_more,   # Whether there are more pages available
        page=page,           # Current page number
        per_page=per_page,   # Number of messages per page
        total_pages=total_pages  # Total number of pages
    )

@router.post("/rooms/{room_id}/read")
async def mark_room_read(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all messages in a room as read"""
    chat_repo = ChatRepository(db)
    success = chat_repo.mark_messages_as_read(room_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Broadcast read status
    await manager.broadcast_message_read(room_id, current_user.id, current_user.name)
    
    return {"status": "success", "message": "Room marked as read"}

@router.put("/messages/{message_id}")
async def update_message(
    message_id: int,
    content: str = Form(..., min_length=1, max_length=5000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a message (only text messages can be updated)"""
    chat_repo = ChatRepository(db)
    
    # Get the message
    message = chat_repo.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is the sender
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own messages")
    
    # Check if message is text type
    if message.message_type != "text":
        raise HTTPException(status_code=400, detail="Only text messages can be updated")
    
    # Update the message
    success = chat_repo.update_message(message_id, content, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get updated message with full details
    updated_message = chat_repo.get_message(message_id)
    other_user = chat_repo.get_room_other_user(updated_message.room_id, current_user.id)
    
    # Build full URLs for files
    file_url = None
    files_data_with_urls = None
    
    if updated_message.file_path:
        from ..config import settings
        # Replace backslashes with forward slashes for web URLs
        clean_path = updated_message.file_path.replace("\\", "/")
        file_url = f"{settings.BASE_URL}/{clean_path}"
    
    if updated_message.files_data:
        from ..config import settings
        files_data_with_urls = []
        for file_data in updated_message.files_data:
            clean_path = file_data["file_path"].replace("\\", "/")
            file_data_with_url = {
                "file_name": file_data["file_name"],
                "file_path": f"{settings.BASE_URL}/{clean_path}",
                "file_size": file_data["file_size"],
                "mime_type": file_data["mime_type"]
            }
            files_data_with_urls.append(file_data_with_url)
    
    # Get sender details
    sender_details = None
    if updated_message.sender:
        is_online = chat_repo.is_user_online(updated_message.sender.id)
        sender_details = {
            "id": updated_message.sender.id,
            "name": updated_message.sender.name,
            "email": updated_message.sender.email,
            "avatar_url": updated_message.sender.avatar_url,
            "is_online": is_online
        }
    
    # Get receiver details
    receiver_details = None
    if updated_message.receiver:
        is_online = chat_repo.is_user_online(updated_message.receiver.id)
        receiver_details = {
            "id": updated_message.receiver.id,
            "name": updated_message.receiver.name,
            "email": updated_message.receiver.email,
            "avatar_url": updated_message.receiver.avatar_url,
            "is_online": is_online
        }
    
    # Create response based on message type
    message_response = {
        "id": updated_message.id,
        "content": updated_message.content,
        "message_type": updated_message.message_type,
        "created_at": updated_message.created_at.isoformat(),
        "is_read": updated_message.is_read,
        "is_deleted": updated_message.is_deleted,
        "is_sender": True,  # Bu message yuboruvchi uchun
        "sender_details": sender_details,
        "receiver_details": receiver_details
    }
    
    # Add file-related fields only if they exist
    if updated_message.file_name:
        message_response["file_name"] = updated_message.file_name
    if file_url:
        message_response["file_path"] = file_url
    if updated_message.file_size:
        message_response["file_size"] = updated_message.file_size
    if files_data_with_urls:
        message_response["files_data"] = files_data_with_urls
    
    # Broadcast updated message to all users in the room
    await manager.broadcast_message_update(
        message_response,
        updated_message.room_id,
        current_user.id,
        updated_message.receiver_id
    )
    
    return message_response

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a message"""
    chat_repo = ChatRepository(db)
    success = chat_repo.delete_message(message_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"status": "success", "message": "Message deleted"}

@router.post("/messages/{message_id}/like", response_model=MessageLikeResponse)
async def toggle_message_like(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle like/unlike for a message"""
    chat_repo = ChatRepository(db)
    result = chat_repo.toggle_message_like(message_id, current_user.id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Message not found or access denied")
    
    return MessageLikeResponse(
        action=result["action"],
        like_count=result["like_count"],
        message_id=message_id
    )

# WebSocket Endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None, room_id: int = None):
    """WebSocket endpoint for real-time chat with authentication and room_id"""
    from ..utils.websocket_auth import authenticate_websocket
    
    # WebSocket connection ni accept qiling
    await websocket.accept()
    
    # Authenticate user
    user = await authenticate_websocket(websocket)
    if not user:
        return  # Connection already closed by authentication function
    
    user_id = user.id
    user_name = user.name
    
    await manager.connect(websocket, user_id)
    
    # If room_id is provided in URL, automatically join the room
    if room_id:
        manager.set_user_room(user_id, room_id)
    
    # Update user presence to online
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        chat_repo = ChatRepository(db)
        chat_repo.update_user_presence(user_id, True)
        
        # Broadcast presence update
        await manager.broadcast_presence(user_id, True, user_name)
    finally:
        db.close()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "typing":
                typing_data = message_data.get("data", {})
                await manager.broadcast_typing(
                    typing_data.get("room_id"),
                    user_id,
                    typing_data.get("is_typing", False),
                    user_name
                )
            
            elif message_data.get("type") == "join_room":
                room_id = message_data.get("data", {}).get("room_id")
                if room_id:
                    manager.set_user_room(user_id, room_id)
            
            elif message_data.get("type") == "leave_room":
                manager.leave_room(user_id)
            
            
            elif message_data.get("type") == "send_message":
                # Handle all message types (text, image, file) through WebSocket
                message_info = message_data.get("data", {})
                # Use room_id from URL if not provided in message
                message_room_id = message_info.get("room_id") or room_id
                receiver_id = message_info.get("receiver_id")
                message_type = message_info.get("message_type", "text")
                content = message_info.get("content", "")
                
                # Handle single file (backward compatibility)
                file_data = message_info.get("file_data")  # Base64 encoded file data
                file_name = message_info.get("file_name")
                file_size = message_info.get("file_size")
                mime_type = message_info.get("mime_type")
                
                # Handle multiple files
                files_data = message_info.get("files_data", [])  # Array of file objects
                
                if not message_room_id or not receiver_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing room_id or receiver_id"
                    }))
                    continue
                
                # Verify user has access to the room
                room = chat_repo.get_room(message_room_id, user_id)
                if not room:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Room not found"
                    }))
                    continue
                
                # Verify receiver is in the room
                other_user = chat_repo.get_room_other_user(room.id, user_id)
                if not other_user or other_user.id != receiver_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid receiver"
                    }))
                    continue
                
                # Handle file upload for image, file, and voice messages
                file_path = None
                processed_files_data = None
                
                # Handle multiple files (new approach)
                if message_type in ["image", "file", "voice"] and files_data:
                    try:
                        import base64
                        import os
                        from datetime import datetime
                        
                        processed_files = []
                        
                        for file_info in files_data:
                            file_data_item = file_info.get("file_data")
                            file_name_item = file_info.get("file_name")
                            file_size_item = file_info.get("file_size")
                            mime_type_item = file_info.get("mime_type")
                            
                            if not file_data_item or not file_name_item:
                                continue
                            
                            # Decode base64 file data
                            file_bytes = base64.b64decode(file_data_item)
                            
                            # Create appropriate directory
                            if message_type == "image":
                                upload_dir = "static/chat_files/images"
                            elif message_type == "voice":
                                upload_dir = "static/chat_files/voices"
                            else:  # file
                                upload_dir = "static/chat_files/files"
                            
                            os.makedirs(upload_dir, exist_ok=True)
                            
                            # Generate unique filename
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            file_extension = os.path.splitext(file_name_item)[1] if file_name_item else ""
                            unique_filename = f"{user_id}_{timestamp}_{len(processed_files)}_{file_name_item}"
                            file_path_item = os.path.join(upload_dir, unique_filename)
                            
                            # Save file
                            with open(file_path_item, "wb") as f:
                                f.write(file_bytes)
                            
                            # Add to processed files
                            processed_files.append({
                                "file_name": file_name_item,
                                "file_path": file_path_item,
                                "file_size": file_size_item or len(file_bytes),
                                "mime_type": mime_type_item
                            })
                        
                        processed_files_data = processed_files
                        
                        # For backward compatibility, set single file fields if only one file
                        if len(processed_files) == 1:
                            single_file = processed_files[0]
                            file_name = single_file["file_name"]
                            file_path = single_file["file_path"]
                            file_size = single_file["file_size"]
                            mime_type = single_file["mime_type"]
                        
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Multiple file upload failed: {str(e)}"
                        }))
                        continue
                
                # Handle single file (backward compatibility)
                elif message_type in ["image", "file", "voice"] and file_data:
                    try:
                        import base64
                        import os
                        from datetime import datetime
                        
                        # Decode base64 file data
                        file_bytes = base64.b64decode(file_data)
                        
                        # Create appropriate directory
                        if message_type == "image":
                            upload_dir = "static/chat_files/images"
                        elif message_type == "voice":
                            upload_dir = "static/chat_files/voices"
                        else:  # file
                            upload_dir = "static/chat_files/files"
                        
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Generate unique filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_extension = os.path.splitext(file_name)[1] if file_name else ""
                        unique_filename = f"{user_id}_{timestamp}_{file_name}"
                        file_path = os.path.join(upload_dir, unique_filename)
                        
                        # Save file
                        with open(file_path, "wb") as f:
                            f.write(file_bytes)
                        
                        # Update file_name to include path
                        file_name = unique_filename
                        
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"File upload failed: {str(e)}"
                        }))
                        continue
                
                # Create message in database
                message = chat_repo.create_message(
                    room_id=message_room_id,
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    message_type=message_type,
                    content=content,
                    file_name=file_name,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type,
                    files_data=processed_files_data
                )
                
                # Build full URLs for files
                file_url = None
                files_data_with_urls = None
                
                if message.file_path:
                    from ..config import settings
                    # Replace backslashes with forward slashes for web URLs
                    clean_path = message.file_path.replace("\\", "/")
                    file_url = f"{settings.BASE_URL}/{clean_path}"
                
                if message.files_data:
                    from ..config import settings
                    files_data_with_urls = []
                    for file_data in message.files_data:
                        clean_path = file_data["file_path"].replace("\\", "/")
                        file_data_with_url = {
                            "file_name": file_data["file_name"],
                            "file_path": f"{settings.BASE_URL}/{clean_path}",
                            "file_size": file_data["file_size"],
                            "mime_type": file_data["mime_type"]
                        }
                        files_data_with_urls.append(file_data_with_url)
                
                # Get sender details
                sender_details = None
                if message.sender:
                    is_online = chat_repo.is_user_online(message.sender.id)
                    sender_details = {
                        "id": message.sender.id,
                        "name": message.sender.name,
                        "email": message.sender.email,
                        "avatar_url": message.sender.avatar_url,
                        "is_online": is_online
                    }
                
                # Get receiver details
                receiver_details = None
                if message.receiver:
                    is_online = chat_repo.is_user_online(message.receiver.id)
                    receiver_details = {
                        "id": message.receiver.id,
                        "name": message.receiver.name,
                        "email": message.receiver.email,
                        "avatar_url": message.receiver.avatar_url,
                        "is_online": is_online
                    }
                
                # Create response based on message type
                message_response = {
                    "id": message.id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "created_at": message.created_at.isoformat(),
                    "is_read": message.is_read,
                    "is_deleted": message.is_deleted,
                    "sender_details": sender_details,
                    "receiver_details": receiver_details
                }
                
                # Add file-related fields only if they exist
                if message.file_name:
                    message_response["file_name"] = message.file_name
                if file_url:
                    message_response["file_path"] = file_url
                if message.file_size:
                    message_response["file_size"] = message.file_size
                if files_data_with_urls:
                    message_response["files_data"] = files_data_with_urls
                
                # Broadcast message to all users in the room
                await manager.broadcast_new_message(
                    message_response,
                    message_room_id,
                    user_id,
                    receiver_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        
        # Update user presence to offline
        db = SessionLocal()
        try:
            chat_repo = ChatRepository(db)
            chat_repo.update_user_presence(user_id, False)
            
            # Get user info for presence broadcast
            user = db.query(User).filter(User.id == user_id).first()
            user_name = user.name if user else f"User {user_id}"
            
            # Broadcast presence update
            await manager.broadcast_presence(user_id, False, user_name)
        finally:
            db.close()

# Utility Endpoints
@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread message count for all rooms"""
    chat_repo = ChatRepository(db)
    unread_counts = chat_repo.get_unread_count(current_user.id)
    return {"unread_counts": unread_counts}

@router.get("/online-users", response_model=OnlineUsersResponse)
async def get_online_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of online users who are in the same chat rooms as the current user"""
    chat_repo = ChatRepository(db)
    online_users = chat_repo.get_online_users_in_rooms(current_user.id)
    
    # Get presence information for each user
    online_user_details = []
    for user in online_users:
        presence = chat_repo.get_user_presence(user.id)
        last_seen = presence.last_seen if presence else user.last_login or user.created_at
        
        online_user_details.append(OnlineUserDetails(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            phone=user.phone,
            about_me=user.about_me,
            current_position=user.current_position,
            is_verified=user.is_verified,
            last_seen=last_seen,
            is_online=True
        ))
    
    return OnlineUsersResponse(online_users=online_user_details)

@router.get("/check-room", response_model=RoomCheckResponse)
async def check_user_room(
    user_id: int = Query(..., description="ID of the user to check room with"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if current user has a chat room with another user"""
    chat_repo = ChatRepository(db)
    
    # Check if other user exists
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        return RoomCheckResponse(
            status="error",
            msg="User not found",
            data=[]
        )
    
    # Check if room exists between users
    room = chat_repo.get_direct_room(current_user.id, user_id)
    
    if not room:
        return RoomCheckResponse(
            status="success",
            msg="No room found between users",
            data=[]
        )
    
    # Get other user info
    is_online = chat_repo.is_user_online(other_user.id)
    other_user_info = {
        "id": other_user.id,
        "name": other_user.name,
        "email": other_user.email,
        "avatar_url": other_user.avatar_url,
        "is_online": is_online
    }
    
    # Get last message
    last_message = chat_repo.get_last_message(room.id)
    last_message_info = None
    if last_message:
        last_message_info = {
            "id": last_message.id,
            "content": last_message.content,
            "message_type": last_message.message_type,
            "created_at": last_message.created_at,
            "sender_name": last_message.sender.name
        }
    
    # Get unread count
    unread_counts = chat_repo.get_unread_count(current_user.id)
    unread_count = unread_counts.get(room.id, 0)
    
    room_data = ChatRoomResponse(
        id=room.id,
        name=room.name,
        room_type=room.room_type,
        created_by=room.created_by,
        created_at=room.created_at,
        updated_at=room.updated_at,
        is_active=room.is_active,
        other_user=other_user_info,
        last_message=last_message_info,
        unread_count=unread_count
    )
    
    return RoomCheckResponse(
        status="success",
        msg="Room found",
        data=[room_data]
    )


# Test WebSocket endpoint (no authentication)
@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Test WebSocket endpoint without authentication"""
    try:
        await websocket.accept()
        print("WebSocket connection accepted")
        
        # Test user data
        user_id = 1
        user_name = "Test User"
        
        await manager.connect(websocket, user_id)
        print(f"User {user_id} connected to manager")
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "Connected to test WebSocket",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                print(f"Received message: {message_data}")
                
                # Echo back the message
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "data": message_data,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                print(f"Error processing message: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            manager.disconnect(user_id)
            print(f"Test user {user_id} disconnected")
        except:
            pass

@router.post("/video-call/token", response_model=VideoCallTokenResponse)
async def generate_video_call_token(
    current_user: User = Depends(get_current_user)
):
    """Generate Agora RTC token for video calling - Production Mode"""
    try:
        # Auto-generate channel name based on user and timestamp
        import time
        timestamp = int(time.time())
        channel_name = f"user_{current_user.id}_call_{timestamp}"
        
        # Use user email as user_account, or generate UUID if no email
        user_account = current_user.email if current_user.email else f"user_{current_user.id}_{uuid.uuid4().hex[:8]}"
        
        # Generate real token using Agora with auto-generated values
        token_data = generate_rtc_token(
            channel_name=channel_name,
            uid=None,  # Use user_account instead
            user_account=user_account,
            role="publisher",  # Default role
            expire_seconds=3600  # Default 1 hour
        )
        
        return VideoCallTokenResponse(
            app_id=token_data["appId"],
            channel=token_data["channel"],
            uid=token_data["uid"],
            user_account=token_data["userAccount"],
            role=token_data["role"],
            expire_at=token_data["expireAt"],
            token=token_data["token"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token generation failed: {str(e)}")

@router.post("/video-call/start", response_model=VideoCallResponse)
async def start_video_call(
    call_request: VideoCallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a video call with another user"""
    chat_repo = ChatRepository(db)
    
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == call_request.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate unique call ID
    call_id = str(uuid.uuid4())
    
    # Generate token for the caller
    try:
        token_data = generate_rtc_token(
            channel_name=call_request.channel_name,
            uid=current_user.id,
            role="publisher",
            expire_seconds=3600
        )
        
        token_response = VideoCallTokenResponse(
            app_id=token_data["appId"],
            channel=token_data["channel"],
            uid=token_data["uid"],
            user_account=token_data["userAccount"],
            role=token_data["role"],
            expire_at=token_data["expireAt"],
            token=token_data["token"]
        )
        
        # Create video call message in database
        # First, create or get room between users
        room = chat_repo.create_direct_room(current_user.id, call_request.receiver_id)
        
        # Create video call message
        message = chat_repo.create_message(
            room_id=room.id,
            sender_id=current_user.id,
            receiver_id=call_request.receiver_id,
            message_type="video_call",
            content=f"Video call started in channel: {call_request.channel_name}",
            file_name=None,
            file_path=None,
            file_size=None,
            mime_type=None
        )
        
        # Broadcast video call notification via WebSocket
        await manager.broadcast_video_call(
            call_id=call_id,
            channel_name=call_request.channel_name,
            caller_id=current_user.id,
            caller_name=current_user.name,
            receiver_id=call_request.receiver_id,
            room_id=room.id
        )
        
        return VideoCallResponse(
            call_id=call_id,
            channel_name=call_request.channel_name,
            token=token_response,
            receiver_id=call_request.receiver_id,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to start video call: {str(e)}")

@router.post("/video-call/answer/{call_id}")
async def answer_video_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a video call"""
    # Generate token for the receiver
    try:
        # For now, we'll use a simple channel name based on call_id
        channel_name = f"call_{call_id}"
        
        token_data = generate_rtc_token(
            channel_name=channel_name,
            uid=current_user.id,
            role="publisher",
            expire_seconds=3600
        )
        
        # Broadcast call answered notification
        await manager.broadcast_video_call_answer(
            call_id=call_id,
            receiver_id=current_user.id,
            receiver_name=current_user.name
        )
        
        return {
            "status": "answered",
            "call_id": call_id,
            "token": VideoCallTokenResponse(
                app_id=token_data["appId"],
                channel=token_data["channel"],
                uid=token_data["uid"],
                user_account=token_data["userAccount"],
                role=token_data["role"],
                expire_at=token_data["expireAt"],
                token=token_data["token"]
            )
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to answer video call: {str(e)}")

@router.post("/video-call/reject/{call_id}")
async def reject_video_call(
    call_id: str,
    current_user: User = Depends(get_current_user)
):
    """Reject a video call"""
    # Broadcast call rejected notification
    await manager.broadcast_video_call_reject(
        call_id=call_id,
        receiver_id=current_user.id,
        receiver_name=current_user.name
    )
    
    return {"status": "rejected", "call_id": call_id}

@router.post("/video-call/end/{call_id}")
async def end_video_call(
    call_id: str,
    current_user: User = Depends(get_current_user)
):
    """End a video call"""
    # Broadcast call ended notification
    await manager.broadcast_video_call_end(
        call_id=call_id,
        user_id=current_user.id,
        user_name=current_user.name
    )
    
    return {"status": "ended", "call_id": call_id}

# Test endpoints (no authentication required)
@router.post("/video-call/token/test", response_model=VideoCallTokenResponse)
async def generate_video_call_token_test(
    token_request: VideoCallTokenRequest
):
    """Generate Agora RTC token for video calling (TEST - No Auth) - Production Mode"""
    try:
        # Generate real token using Agora
        token_data = generate_rtc_token(
            channel_name=token_request.channel_name,
            uid=token_request.uid,
            user_account=token_request.user_account,
            role=token_request.role,
            expire_seconds=token_request.expire_seconds
        )
        
        return VideoCallTokenResponse(
            app_id=token_data["appId"],
            channel=token_data["channel"],
            uid=token_data["uid"],
            user_account=token_data["userAccount"],
            role=token_data["role"],
            expire_at=token_data["expireAt"],
            token=token_data["token"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token generation failed: {str(e)}")

# Test WebSocket endpoint (no authentication)
@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Test WebSocket endpoint without authentication"""
    try:
        await websocket.accept()
        print("WebSocket connection accepted")
        
        # Test user data
        user_id = 1
        user_name = "Test User"
        
        await manager.connect(websocket, user_id)
        print(f"User {user_id} connected to manager")
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "Connected to test WebSocket",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                print(f"Received message: {message_data}")
                
                # Echo back the message
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "data": message_data,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                print(f"Error processing message: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            manager.disconnect(user_id)
            print(f"Test user {user_id} disconnected")
        except:
            pass