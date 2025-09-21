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
    FileUploadResponse, WebSocketMessage, TypingIndicator, UserPresenceUpdate
)
from ..utils.websocket_manager import manager
from ..utils.file_upload import file_upload_manager
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter()

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
    
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == room_data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create or get existing room
    room = chat_repo.create_direct_room(current_user.id, room_data.receiver_id)
    
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
        message_responses.append(ChatMessageResponse(
            id=message.id,
            room_id=message.room_id,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            sender_name=message.sender.name,
            receiver_name=message.receiver.name,
            sender_avatar=message.sender.avatar_url,
            receiver_avatar=message.receiver.avatar_url,
            message_type=message.message_type,
            content=message.content,
            file_name=message.file_name,
            file_path=message.file_path,
            file_size=message.file_size,
            mime_type=message.mime_type,
            created_at=message.created_at,
            is_read=message.is_read,
            is_deleted=message.is_deleted
        ))
    
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
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a room"""
    chat_repo = ChatRepository(db)
    
    # Verify user has access to the room
    room = chat_repo.get_room(room_id, current_user.id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    messages = chat_repo.get_room_messages(room_id, current_user.id, page, per_page)
    
    message_responses = []
    for message in messages:
        message_responses.append(ChatMessageResponse(
            id=message.id,
            room_id=message.room_id,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            sender_name=message.sender.name,
            receiver_name=message.receiver.name,
            sender_avatar=message.sender.avatar_url,
            receiver_avatar=message.receiver.avatar_url,
            message_type=message.message_type,
            content=message.content,
            file_name=message.file_name,
            file_path=message.file_path,
            file_size=message.file_size,
            mime_type=message.mime_type,
            created_at=message.created_at,
            is_read=message.is_read,
            is_deleted=message.is_deleted
        ))
    
    return MessageListResponse(
        messages=message_responses,
        total=len(message_responses),
        has_more=len(message_responses) == per_page
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
    
    # Create response
    message_response = {
        "id": updated_message.id,
        "room_id": updated_message.room_id,
        "sender_id": updated_message.sender_id,
        "receiver_id": updated_message.receiver_id,
        "sender_name": current_user.name,
        "receiver_name": other_user.name if other_user else "Unknown",
        "sender_avatar": current_user.avatar_url,
        "receiver_avatar": other_user.avatar_url if other_user else None,
        "message_type": updated_message.message_type,
        "content": updated_message.content,
        "file_name": updated_message.file_name,
        "file_path": updated_message.file_path,
        "file_size": updated_message.file_size,
        "mime_type": updated_message.mime_type,
        "created_at": updated_message.created_at.isoformat(),
        "updated_at": updated_message.updated_at.isoformat() if updated_message.updated_at else None,
        "is_read": updated_message.is_read,
        "is_deleted": updated_message.is_deleted,
        "is_edited": updated_message.is_edited
    }
    
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

# WebSocket Endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with authentication"""
    from ..utils.websocket_auth import authenticate_websocket
    
    # Authenticate the WebSocket connection
    user = await authenticate_websocket(websocket)
    if not user:
        return  # Connection already closed by authentication function
    
    user_id = user.id
    user_name = user.name
    
    await manager.connect(websocket, user_id)
    
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
                room_id = message_info.get("room_id")
                receiver_id = message_info.get("receiver_id")
                message_type = message_info.get("message_type", "text")
                content = message_info.get("content", "")
                file_data = message_info.get("file_data")  # Base64 encoded file data
                file_name = message_info.get("file_name")
                file_size = message_info.get("file_size")
                mime_type = message_info.get("mime_type")
                
                if not room_id or not receiver_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing room_id or receiver_id"
                    }))
                    continue
                
                # Verify user has access to the room
                room = chat_repo.get_room(room_id, user_id)
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
                
                # Handle file upload for image and file messages
                file_path = None
                if message_type in ["image", "file"] and file_data:
                    try:
                        import base64
                        import os
                        from datetime import datetime
                        
                        # Decode base64 file data
                        file_bytes = base64.b64decode(file_data)
                        
                        # Create appropriate directory
                        if message_type == "image":
                            upload_dir = "static/chat_files/images"
                        else:
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
                    room_id=room_id,
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    message_type=message_type,
                    content=content,
                    file_name=file_name,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type
                )
                
                # Create response
                message_response = {
                    "id": message.id,
                    "room_id": message.room_id,
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "sender_name": user_name,
                    "receiver_name": other_user.name,
                    "sender_avatar": user.avatar_url,
                    "receiver_avatar": other_user.avatar_url,
                    "message_type": message.message_type,
                    "content": message.content,
                    "file_name": message.file_name,
                    "file_path": message.file_path,
                    "file_size": message.file_size,
                    "mime_type": message.mime_type,
                    "created_at": message.created_at.isoformat(),
                    "is_read": message.is_read,
                    "is_deleted": message.is_deleted
                }
                
                # Broadcast message to all users in the room
                await manager.broadcast_new_message(
                    message_response,
                    room_id,
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

@router.get("/online-users")
async def get_online_users(db: Session = Depends(get_db)):
    """Get list of currently online users"""
    chat_repo = ChatRepository(db)
    online_users = chat_repo.get_online_users()
    
    return {
        "online_users": [
            {
                "user_id": user.user_id,
                "last_seen": user.last_seen,
                "is_online": user.is_online
            }
            for user in online_users
        ]
    }
