from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ..db.database import get_db
from ..repositories.chat_repository import ChatRepository
from ..schemas.chat import (
    UserSearchResponse, UserSearchListResponse,
    ChatRoomResponse, ChatRoomCreate, ChatRoomListResponse,
    ChatMessageResponse, ChatMessageCreate, TextMessageCreate, MessageListResponse,
    WebSocketMessage, TypingIndicator, UserPresenceUpdate,
    VideoCallTokenRequest, VideoCallTokenResponse, VideoCallRequest, VideoCallResponse, VideoCallStatus,
    MessageLikeRequest, MessageLikeResponse, RoomCheckResponse,
    OnlineUsersResponse, OnlineUserDetails,
    ChatRoomDetailResponse, ChatParticipantResponse
)
from ..utils.websocket_manager import manager
from ..utils.file_upload import file_upload_manager
from ..utils.auth import get_current_user
from ..utils.agora_tokens_standalone import generate_rtc_token
from ..models.user import User
from ..models.user_device_token import UserDeviceToken
from ..utils.firebase_notifications import send_push_notification_multiple
import uuid

router = APIRouter(tags=["Chat"])

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
        from ..core.logging_config import logger
        logger.error(f"Chat notification error getting device tokens: {str(e)}", exc_info=True)
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

def send_chat_notification(
    db: Session,
    recipient_user_id: int,
    sender_name: str,
    message_content: str,
    message_type: str,
    room_id: int,
    message_id: int,
    sender_id: int
):
    """Send push notification for chat message"""
    try:
        device_tokens = get_user_device_tokens(db, recipient_user_id)
        print(f"[Chat Notification] Found {len(device_tokens)} device token(s) for user_id={recipient_user_id}")

        if device_tokens:
            if message_type == "text":
                title = f"New message from {sender_name}"
                body = message_content[:100] if message_content else "New message"
            elif message_type == "image":
                title = f"New image from {sender_name}"
                body = f"{sender_name} sent an image"
            elif message_type == "voice":
                title = f"New voice message from {sender_name}"
                body = f"{sender_name} sent a voice message"
            elif message_type == "file":
                title = f"New file from {sender_name}"
                body = f"{sender_name} sent a file"
            else:
                title = f"New message from {sender_name}"
                body = f"{sender_name} sent a message"

            print(f"[Chat Notification] Sending notification - Title: {title}, Body: {body}, Type: {message_type}")

            try:
                result = send_push_notification_multiple(
                    device_tokens=device_tokens,
                    title=title,
                    body=body,
                    data={
                        "type": "chat_message",
                        "room_id": str(room_id),
                        "message_id": str(message_id),
                        "sender_id": str(sender_id),
                        "chat_message_type": message_type
                    },
                    sound="default"
                )
                skipped = result.get('skipped_count', 0)
                failed = result.get('failure_count', 0)
                success = result.get('success_count', 0)

                print(f"[Chat Notification] Result - Success: {success}, Failed: {failed}, Skipped: {skipped}")

                if failed > 0:
                    for item in result.get("results", []):
                        if not item.get("success"):
                            print(f"[Chat Notification] Device token error: token={item.get('token')}, error={item.get('error')}")
            except FileNotFoundError as fe:
                print(f"[Chat Notification] WARNING: Firebase service account file not found. Push notification skipped, but notification is saved to database: {str(fe)}")
            except Exception as fe:
                print(f"[Chat Notification] WARNING: Failed to send push notification (notification saved to database): {str(fe)}")
    except Exception as e:
        print(f"[Chat Notification] WARNING: Failed to send notification to user_id={recipient_user_id}: {str(e)}")

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

@router.post("/rooms", response_model=ChatRoomResponse)
async def create_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a direct chat room with another user"""
    chat_repo = ChatRepository(db)
    
    if room_data.receiver_id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail="You cannot create a room with yourself"
        )
    
    receiver = db.query(User).filter(
        User.id == room_data.receiver_id,
        User.is_active == True
    ).first()
    if not receiver:
        raise HTTPException(
            status_code=404, 
            detail="User not found or inactive"
        )
    
    existing_room = chat_repo.get_direct_room(current_user.id, room_data.receiver_id)
    if existing_room:
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
    
    try:
        room = chat_repo.create_direct_room(current_user.id, room_data.receiver_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create room: {str(e)}"
        )
    
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
    
    unread_counts = chat_repo.get_unread_count(current_user.id)
    
    room_responses = []
    for room in rooms:
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
    
    unread_counts = chat_repo.get_unread_count(current_user.id)
    unread_count = unread_counts.get(room.id, 0)
    
    messages = chat_repo.get_room_messages(room_id, current_user.id, page=1, per_page=1000)
    
    message_responses = []
    for message in messages:
        is_sender = message.sender_id == current_user.id
        
        is_liked = chat_repo.is_message_liked_by_user(message.id, current_user.id)
        like_count = chat_repo.get_message_like_count(message.id)
        
        file_url = None
        files_data_with_urls = None
        
        if message.file_path:
            from ..core.config import settings
            clean_path = message.file_path.replace("\\", "/")
            file_url = f"{settings.BASE_URL}/{clean_path}"
        
        if message.files_data:
            from ..core.config import settings
            files_data_with_urls = []
            for file_data in message.files_data:
                clean_path = file_data["file_path"].replace("\\", "/")
                file_data_with_url = {
                    "file_name": file_data["file_name"],
                    "file_path": f"{settings.BASE_URL}/{clean_path}",
                    "file_size": file_data["file_size"],
                    "mime_type": file_data["mime_type"]
                }
                if "duration" in file_data and file_data["duration"] is not None:
                    file_data_with_url["duration"] = file_data["duration"]
                files_data_with_urls.append(file_data_with_url)
        
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
        
        message_response = {
            "id": message.id,
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
            "is_read": message.is_read,
            "is_deleted": message.is_deleted,
            "is_sender": is_sender,
            "is_liked": is_liked,
            "like_count": like_count,
            "sender_details": sender_details,
            "receiver_details": receiver_details,
            "local_temp_id": None,
            "files_data": files_data_with_urls if files_data_with_urls else None,
            "duration": message.duration if message.duration else None
        }
        
        if message.file_name:
            message_response["file_name"] = message.file_name
        if file_url:
            message_response["file_path"] = file_url
        if message.file_size:
            message_response["file_size"] = message.file_size
            
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
    
    room = chat_repo.get_room(room_id, current_user.id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    total_count = chat_repo.get_room_messages_count(room_id, current_user.id)
    
    messages = chat_repo.get_room_messages(room_id, current_user.id, page, per_page)
    
    message_responses = []
    for message in messages:
        is_sender = message.sender_id == current_user.id
        
        is_liked = chat_repo.is_message_liked_by_user(message.id, current_user.id)
        like_count = chat_repo.get_message_like_count(message.id)
        
        file_url = None
        files_data_with_urls = None
        
        if message.file_path:
            from ..core.config import settings
            clean_path = message.file_path.replace("\\", "/")
            file_url = f"{settings.BASE_URL}/{clean_path}"
        
        if message.files_data:
            from ..core.config import settings
            files_data_with_urls = []
            for file_data in message.files_data:
                clean_path = file_data["file_path"].replace("\\", "/")
                file_data_with_url = {
                    "file_name": file_data["file_name"],
                    "file_path": f"{settings.BASE_URL}/{clean_path}",
                    "file_size": file_data["file_size"],
                    "mime_type": file_data["mime_type"]
                }
                if "duration" in file_data and file_data["duration"] is not None:
                    file_data_with_url["duration"] = file_data["duration"]
                files_data_with_urls.append(file_data_with_url)
        
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
            "receiver_details": receiver_details,
            "local_temp_id": None,
            "files_data": files_data_with_urls if files_data_with_urls else None
        }
        
        if message.file_name:
            message_data["file_name"] = message.file_name
        if file_url:
            message_data["file_path"] = file_url
        if message.file_size:
            message_data["file_size"] = message.file_size
            
        message_responses.append(ChatMessageResponse(**message_data))
    
    total_pages = (total_count + per_page - 1) // per_page
    has_more = page < total_pages
    
    return MessageListResponse(
        messages=message_responses,
        total=total_count,
        has_more=has_more,
        page=page,
        per_page=per_page,
        total_pages=total_pages
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
    
    message = chat_repo.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own messages")
    
    if message.message_type != "text":
        raise HTTPException(status_code=400, detail="Only text messages can be updated")
    
    success = chat_repo.update_message(message_id, content, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    
    updated_message = chat_repo.get_message(message_id)
    other_user = chat_repo.get_room_other_user(updated_message.room_id, current_user.id)
    
    file_url = None
    files_data_with_urls = None
    
    if updated_message.file_path:
        from ..core.config import settings
        clean_path = updated_message.file_path.replace("\\", "/")
        file_url = f"{settings.BASE_URL}/{clean_path}"
    
    if updated_message.files_data:
        from ..core.config import settings
        files_data_with_urls = []
        for file_data in updated_message.files_data:
            clean_path = file_data["file_path"].replace("\\", "/")
            file_data_with_url = {
                "file_name": file_data["file_name"],
                "file_path": f"{settings.BASE_URL}/{clean_path}",
                "file_size": file_data["file_size"],
                "mime_type": file_data["mime_type"]
            }
            if "duration" in file_data and file_data["duration"] is not None:
                file_data_with_url["duration"] = int(file_data["duration"])
            files_data_with_urls.append(file_data_with_url)
    
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
    
    message_response = {
        "id": updated_message.id,
        "content": updated_message.content,
        "message_type": updated_message.message_type,
        "created_at": updated_message.created_at.isoformat(),
        "is_read": updated_message.is_read,
        "is_deleted": updated_message.is_deleted,
        "is_sender": True,
        "sender_details": sender_details,
        "receiver_details": receiver_details,
        "local_temp_id": None,
        "files_data": files_data_with_urls if files_data_with_urls else None,
        "duration": updated_message.duration if updated_message.duration else None
    }
    
    if updated_message.file_name:
        message_response["file_name"] = updated_message.file_name
    if file_url:
        message_response["file_path"] = file_url
    if updated_message.file_size:
        message_response["file_size"] = updated_message.file_size
    
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

async def _websocket_endpoint_handler(websocket: WebSocket):
    """WebSocket endpoint handler for real-time chat with authentication and room_id"""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        token = websocket.query_params.get("token")
        room_id = websocket.query_params.get("room_id")
        
        if not token:
            query_string = websocket.url.query
            if query_string:
                params = {}
                for param in query_string.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        params[key] = value
                    elif "-" in param:
                        if param.startswith("token-"):
                            token = param.replace("token-", "", 1)
                if not token:
                    token = params.get("token")
                if not room_id:
                    room_id = params.get("room_id")
        
        if room_id:
            try:
                room_id = int(room_id)
            except:
                room_id = None
        
        from ..utils.websocket_auth import authenticate_websocket
        from ..utils.auth import verify_token
        from ..db.database import SessionLocal
        from ..models.user import User
        
        await websocket.accept()
        
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return
        
        payload = verify_token(token)
        
        if not payload:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return
        
        token_type = payload.get("type")
        
        if token_type and token_type != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
        
        user_id = payload.get("sub") or payload.get("user_id")
        
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token payload - no user_id")
            return
        
        db = SessionLocal()
        user = None
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            
            if not user:
                await websocket.close(code=4001, reason="User not found")
                return
            
            if not user.is_active:
                await websocket.close(code=4001, reason="User account is inactive")
                return
        finally:
            db.close()
        
        user_id = user.id
        user_name = user.name
        
    except Exception as e:
        print(f"WebSocket auth error ({type(e).__name__}): {str(e)}")
        traceback.print_exc()
        try:
            await websocket.close(code=4000, reason=f"Authentication error: {str(e)}")
        except Exception as close_error:
            print(f"WebSocket error while closing connection: {close_error}")
        return
    
    await manager.connect(websocket, user_id)
    
    if room_id:
        manager.set_user_room(user_id, room_id)
    
    from ..db.database import SessionLocal
    db = SessionLocal()
    try:
        chat_repo = ChatRepository(db)
        chat_repo.update_user_presence(user_id, True)
        
        await manager.broadcast_presence(user_id, True, user_name)
    finally:
        db.close()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                import re
                original_data = data
                data = re.sub(r'/\*.*?\*/', '', data, flags=re.DOTALL)
                
                lines = data.split('\n')
                cleaned_lines = []
                in_string = False
                escape_next = False
                
                for line in lines:
                    cleaned_line = ""
                    i = 0
                    while i < len(line):
                        char = line[i]
                        
                        if escape_next:
                            cleaned_line += char
                            escape_next = False
                            i += 1
                            continue
                        
                        if char == '\\':
                            cleaned_line += char
                            escape_next = True
                            i += 1
                            continue
                        
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            cleaned_line += char
                            i += 1
                            continue
                        
                        if not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                            break
                        
                        cleaned_line += char
                        i += 1
                    
                    cleaned_lines.append(cleaned_line)
                
                data = '\n'.join(cleaned_lines)
                data = re.sub(r',(\s*[}\]])', r'\1', data)
                data = re.sub(r'\s+([}\]])', r'\1', data)

                message_data = json.loads(data)
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Invalid JSON format: {str(e)}"
                }))
                continue
            
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
                message_info = message_data.get("data", {})
                message_room_id = message_info.get("room_id") or room_id
                receiver_id = message_info.get("receiver_id")
                message_type = message_info.get("message_type", "text")
                content = message_info.get("content", "")
                local_temp_id = message_info.get("local_temp_id")
                
                files_data = message_info.get("files_data", [])
                
                if not message_room_id or not receiver_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Missing room_id or receiver_id"
                    }))
                    continue
                
                from ..db.database import SessionLocal
                message_db = SessionLocal()
                try:
                    chat_repo = ChatRepository(message_db)
                
                    room = chat_repo.get_room(message_room_id, user_id)
                    if not room:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Room not found"
                        }))
                        continue
                    
                    other_user = chat_repo.get_room_other_user(room.id, user_id)
                    if not other_user or other_user.id != receiver_id:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Invalid receiver"
                        }))
                        continue
                
                    processed_files_data = None
                    
                    MAX_IMAGE_SIZE = 10 * 1024 * 1024
                    MAX_FILE_SIZE = 50 * 1024 * 1024
                    MAX_VOICE_SIZE = 50 * 1024 * 1024
                    
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
                                duration_item = file_info.get("duration")
                                
                                if not file_data_item or not file_name_item:
                                    continue
                                
                                try:
                                    file_data_item = file_data_item.strip()
                                    
                                    missing_padding = len(file_data_item) % 4
                                    if missing_padding:
                                        file_data_item += '=' * (4 - missing_padding)
                                    
                                    file_bytes = base64.b64decode(file_data_item, validate=True)
                                except Exception as decode_error:
                                    await websocket.send_text(json.dumps({
                                        "type": "error",
                                        "message": f"Invalid base64 data for file '{file_name_item}': {str(decode_error)}"
                                    }))
                                    continue
                                
                                max_size = MAX_IMAGE_SIZE if message_type == "image" else (MAX_VOICE_SIZE if message_type == "voice" else MAX_FILE_SIZE)
                                if len(file_bytes) > max_size:
                                    size_mb = max_size / (1024 * 1024)
                                    await websocket.send_text(json.dumps({
                                        "type": "error",
                                        "message": f"File '{file_name_item}' too large. Maximum size: {size_mb:.1f}MB"
                                    }))
                                    continue
                                
                                if message_type == "image":
                                    upload_dir = "static/chat_files/images"
                                elif message_type == "voice":
                                    upload_dir = "static/chat_files/voices"
                                else:
                                    upload_dir = "static/chat_files/files"
                                
                                os.makedirs(upload_dir, exist_ok=True)
                                
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                unique_filename = f"{user_id}_{timestamp}_{len(processed_files)}_{file_name_item}"
                                file_path_item = os.path.join(upload_dir, unique_filename)
                                
                                with open(file_path_item, "wb") as f:
                                    f.write(file_bytes)
                                
                                file_data = {
                                    "file_name": file_name_item,
                                    "file_path": file_path_item,
                                    "file_size": file_size_item or len(file_bytes),
                                    "mime_type": mime_type_item
                                }
                                
                                if message_type == "voice" and duration_item is not None:
                                    file_data["duration"] = int(duration_item)
                                
                                processed_files.append(file_data)
                            
                            processed_files_data = processed_files if processed_files else None
                            
                            duration = None
                            if processed_files_data and len(processed_files_data) == 1:
                                single_file = processed_files_data[0]
                                file_name = single_file["file_name"]
                                file_path = single_file["file_path"]
                                file_size = single_file["file_size"]
                                mime_type = single_file["mime_type"]
                                duration = single_file.get("duration")
                            
                        except Exception as e:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": f"File upload failed: {str(e)}"
                            }))
                            continue
                
                    file_name = None
                    file_path = None
                    file_size = None
                    mime_type = None
                    duration = None
                    
                    if processed_files_data and len(processed_files_data) == 1:
                        single_file = processed_files_data[0]
                        file_name = single_file["file_name"]
                        file_path = single_file["file_path"]
                        file_size = single_file["file_size"]
                        mime_type = single_file["mime_type"]
                        duration = single_file.get("duration")
                    
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
                    duration=duration,
                    files_data=processed_files_data
                )
                
                    files_data_with_urls = None
                    
                    if message.files_data:
                        from ..core.config import settings
                        files_data_with_urls = []
                        for file_data in message.files_data:
                            clean_path = file_data["file_path"].replace("\\", "/")
                            file_data_with_url = {
                                "file_name": file_data["file_name"],
                                "file_path": f"{settings.BASE_URL}/{clean_path}",
                                "file_size": file_data["file_size"],
                                "mime_type": file_data["mime_type"]
                            }
                            if "duration" in file_data and file_data["duration"] is not None:
                                file_data_with_url["duration"] = int(file_data["duration"])
                            files_data_with_urls.append(file_data_with_url)
                    
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
                    
                    message_response = {
                        "id": message.id,
                        "content": message.content,
                        "message_type": message.message_type,
                        "created_at": message.created_at.isoformat(),
                        "is_read": message.is_read,
                        "is_deleted": message.is_deleted,
                        "sender_details": sender_details,
                        "receiver_details": receiver_details,
                        "local_temp_id": local_temp_id if local_temp_id else None,
                        "files_data": files_data_with_urls if files_data_with_urls else None,
                        "duration": message.duration if message.duration else None
                    }
                    
                    try:
                        from ..repositories.notification_repository import NotificationRepository
                        from ..models.notification import NotificationType
                        from ..db.database import SessionLocal
                        
                        notification_db = SessionLocal()
                        try:
                            notification_repo = NotificationRepository(notification_db)
                            
                            sender_name = user_name
                            if message_type == "text":
                                notification_title = f"New message from {sender_name}"
                                notification_body = content[:100] if content else "New message"
                            elif message_type == "image":
                                notification_title = f"New image from {sender_name}"
                                notification_body = f"{sender_name} sent an image"
                            elif message_type == "voice":
                                notification_title = f"New voice message from {sender_name}"
                                notification_body = f"{sender_name} sent a voice message"
                            elif message_type == "file":
                                notification_title = f"New file from {sender_name}"
                                notification_body = f"{sender_name} sent a file"
                            else:
                                notification_title = f"New message from {sender_name}"
                                notification_body = f"{sender_name} sent a message"
                            
                            notification_repo.create(
                                type=NotificationType.MESSAGE_RECEIVED,
                                title=notification_title,
                                body=notification_body,
                                recipient_user_id=receiver_id,
                                room_id=message_room_id,
                                message_id=message.id,
                                sender_id=user_id
                            )
                            
                            send_chat_notification(
                                db=notification_db,
                                recipient_user_id=receiver_id,
                                sender_name=sender_name,
                                message_content=content or "",
                                message_type=message_type,
                                room_id=message_room_id,
                                message_id=message.id,
                                sender_id=user_id
                            )
                        finally:
                            notification_db.close()
                    except Exception as e:
                        print(f"Chat notification: failed to create/send notification: {str(e)}")
                
                    await manager.broadcast_new_message(
                        message_response,
                        message_room_id,
                        user_id,
                        receiver_id
                    )
                finally:
                    message_db.close()
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        
        db = SessionLocal()
        try:
            chat_repo = ChatRepository(db)
            chat_repo.update_user_presence(user_id, False)
            
            user = db.query(User).filter(User.id == user_id).first()
            user_name = user.name if user else f"User {user_id}"
            
            await manager.broadcast_presence(user_id, False, user_name)
        finally:
            db.close()

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
    
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        return RoomCheckResponse(
            status="error",
            msg="User not found",
            data=[]
        )
    
    room = chat_repo.get_direct_room(current_user.id, user_id)
    
    if not room:
        return RoomCheckResponse(
            status="success",
            msg="No room found between users",
            data=[]
        )
    
    is_online = chat_repo.is_user_online(other_user.id)
    other_user_info = {
        "id": other_user.id,
        "name": other_user.name,
        "email": other_user.email,
        "avatar_url": other_user.avatar_url,
        "is_online": is_online
    }
    
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


@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat room (soft delete)"""
    chat_repo = ChatRepository(db)
    
    # Check if room exists and user is a participant
    room = chat_repo.get_room(room_id, current_user.id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or you are not a participant")
    
    # Get participants BEFORE deleting the room (because get_room_participants checks is_active)
    participants = chat_repo.get_room_participants(room_id)
    
    # Delete the room
    success = chat_repo.delete_room(room_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Notify other participants via WebSocket
    for participant_id in participants:
        if participant_id != current_user.id:
            await manager.broadcast_room_deleted(room_id, current_user.id, current_user.name, participant_id)
    
    return {
        "status": "success",
        "message": "Room deleted successfully",
        "room_id": room_id
    }


@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Test WebSocket endpoint without authentication"""
    try:
        await websocket.accept()
        print("WebSocket connection accepted")
        
        user_id = 1
        user_name = "Test User"
        
        await manager.connect(websocket, user_id)
        print(f"User {user_id} connected to manager")
        
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

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint /ws"""
    await _websocket_endpoint_handler(websocket)

@router.websocket("/ws/")
async def websocket_endpoint_with_slash(websocket: WebSocket):
    """WebSocket endpoint /ws/"""
    await _websocket_endpoint_handler(websocket)

@router.post("/video-call/token", response_model=VideoCallTokenResponse)
async def generate_video_call_token(
    token_request: VideoCallTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate Agora RTC token for video calling.
    
    Channel name is stored in DB, but token is generated fresh on each request
    for better security and to avoid expiry issues.
    """
    from ..models.chat import ChatRoom, ChatParticipant
    from ..models.agora_channel import AgoraChannel
    from sqlalchemy.orm import joinedload
    
    try:
        chat_repo = ChatRepository(db)
        
        # Verify user is participant of the room
        room = chat_repo.get_room(token_request.room_id, current_user.id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found or you are not a participant")
        
        # Get room with participants
        room_with_participants = db.query(ChatRoom).options(
            joinedload(ChatRoom.participants).joinedload(ChatParticipant.user)
        ).filter(ChatRoom.id == token_request.room_id).first()
        
        if not room_with_participants:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get or create channel name
        existing_channel = db.query(AgoraChannel).filter(
            AgoraChannel.room_id == token_request.room_id
        ).first()
        
        if existing_channel:
            channel_name = existing_channel.channel_name
            print(f"Using existing channel_name: {channel_name} for room_id: {token_request.room_id}")
        else:
            # Create new channel name
            channel_name = f"room_{token_request.room_id}_call"
            new_channel = AgoraChannel(
                room_id=token_request.room_id,
                channel_name=channel_name
            )
            db.add(new_channel)
            db.commit()
            db.refresh(new_channel)
            print(f"Created new channel_name: {channel_name} for room_id: {token_request.room_id}")
        
        # Determine UID for token generation
        if token_request.uid is not None and token_request.uid != 0:
            request_uid = token_request.uid
            user_account_for_token = None
        else:
            request_uid = current_user.id
            user_account_for_token = None
        
        # Generate fresh token
        token_data = generate_rtc_token(
            channel_name=channel_name,
            uid=request_uid,
            user_account=user_account_for_token,
            role=token_request.role,
            expire_seconds=token_request.expire_seconds
        )
        
        print(f"Generated fresh token for room_id: {token_request.room_id}, uid: {request_uid}")
        
        # Build participants response
        participants_response = []
        for participant in room_with_participants.participants:
            if participant.is_active and participant.user:
                user_info = UserSearchResponse(
                    id=participant.user.id,
                    name=participant.user.name,
                    email=participant.user.email,
                    avatar_url=participant.user.avatar_url,
                    is_online=chat_repo.is_user_online(participant.user.id)
                )
                participants_response.append(ChatParticipantResponse(
                    id=participant.id,
                    room_id=participant.room_id,
                    user_id=participant.user_id,
                    joined_at=participant.joined_at,
                    last_read_at=participant.last_read_at,
                    is_active=participant.is_active,
                    user=user_info
                ))
        
        room_response = ChatRoomDetailResponse(
            id=room_with_participants.id,
            name=room_with_participants.name,
            room_type=room_with_participants.room_type,
            created_by=room_with_participants.created_by,
            created_at=room_with_participants.created_at,
            updated_at=room_with_participants.updated_at,
            is_active=room_with_participants.is_active,
            participants=participants_response
        )
        
        uid_value = token_data["uid"] if token_data["uid"] is not None else current_user.id
        user_account_value = token_data.get("userAccount")
        
        return VideoCallTokenResponse(
            app_id=token_data["appId"],
            channel=token_data["channel"],
            uid=uid_value,
            user_account=user_account_value,
            role=token_data["role"],
            expire_at=token_data["expireAt"],
            token=token_data["token"],
            room=room_response
        )
    except HTTPException:
        raise
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
    
    receiver = db.query(User).filter(User.id == call_request.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    
    call_id = str(uuid.uuid4())
    
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
        
        room = chat_repo.create_direct_room(current_user.id, call_request.receiver_id)
        
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
    try:
        channel_name = f"call_{call_id}"
        
        token_data = generate_rtc_token(
            channel_name=channel_name,
            uid=current_user.id,
            role="publisher",
            expire_seconds=3600
        )
        
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
    await manager.broadcast_video_call_end(
        call_id=call_id,
        user_id=current_user.id,
        user_name=current_user.name
    )
    
    return {"status": "ended", "call_id": call_id}

@router.post("/video-call/token/test", response_model=VideoCallTokenResponse)
async def generate_video_call_token_test(
    token_request: VideoCallTokenRequest
):
    """
    Generate Agora RTC token for video calling (TEST - No Auth) - Production Mode
    
    Bu endpoint test uchun - authentication talab qilmaydi.
    index.py dagi kodga mos formatda token generate qiladi.
    UUID generate qiladi user_account uchun (production endpoint dagi kabi).
    """
    try:
        # Channel name'ni index.py dagi kabi format qilish
        # Agar room_id bo'lsa, uni ishlatamiz, aks holda custom channel name
        if token_request.room_id:
            channel_name = f"room_{token_request.room_id}_call"
        else:
            # Default channel name (index.py dagi kabi)
            channel_name = "7d72365eb983485397e3e3f9d460bdda"
        
        # UID va user_account'ni index.py dagi kabi handle qilish
        if token_request.uid is not None and token_request.uid != 0:
            # UID berilgan bo'lsa, uni ishlatamiz
            request_uid = token_request.uid
            user_account_for_token = None
        else:
            # UID 0 yoki None bo'lsa, user_account ishlatamiz
            # UUID generate qilish (production endpoint dagi kabi)
            request_uid = None
            if token_request.user_account:
                user_account_for_token = token_request.user_account
            else:
                # UUID generate qilish - production endpoint dagi kabi format
                user_account_for_token = f"test_user_{token_request.room_id}_{uuid.uuid4().hex[:8]}"
        
        # Token generate qilish (index.py dagi generate_rtc_token funksiyasiga mos)
        token_data = generate_rtc_token(
            channel_name=channel_name,
            uid=request_uid,
            user_account=user_account_for_token,
            role=token_request.role,
            expire_seconds=token_request.expire_seconds
        )
        
        # Response format'ni index.py dagi kabi qilish
        uid_value = token_data["uid"] if token_data["uid"] is not None else 0
        
        return VideoCallTokenResponse(
            app_id=token_data["appId"],
            channel=token_data["channel"],
            uid=uid_value,
            user_account=token_data["userAccount"],
            role=token_data["role"],
            expire_at=token_data["expireAt"],
            token=token_data["token"]
        )
    except Exception as e:
        import traceback
        error_detail = f"Token generation failed: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)

@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Test WebSocket endpoint without authentication"""
    try:
        await websocket.accept()
        print("WebSocket connection accepted")
        
        user_id = 1
        user_name = "Test User"
        
        await manager.connect(websocket, user_id)
        print(f"User {user_id} connected to manager")
        
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