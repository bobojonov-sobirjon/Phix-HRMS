from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from ..models.chat import ChatRoom, ChatMessage, ChatParticipant, UserPresence, MessageLike
from ..models.user import User
from ..schemas.chat import ChatRoomCreate, ChatMessageCreate, MessageType
from datetime import datetime, timedelta

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    # User Search
    def search_users_by_email(self, email: str, current_user_id: int, limit: int = 20) -> List[User]:
        """Search users by email (excluding current user)"""
        return self.db.query(User).filter(
            and_(
                User.email.ilike(f"%{email}%"),
                User.id != current_user_id,
                User.is_active == True
            )
        ).limit(limit).all()

    # Chat Room Methods
    def create_direct_room(self, user1_id: int, user2_id: int) -> ChatRoom:
        """Create a direct chat room between two users"""
        # Check if room already exists
        existing_room = self.get_direct_room(user1_id, user2_id)
        if existing_room:
            return existing_room
        
        # Create new room
        from datetime import datetime
        room = ChatRoom(
            name=f"Direct Chat",
            room_type="direct",
            created_by=user1_id,
            updated_at=datetime.utcnow()
        )
        self.db.add(room)
        self.db.flush()  # Get the room ID
        
        # Add both users as participants
        participant1 = ChatParticipant(
            room_id=room.id,
            user_id=user1_id,
            is_active=True
        )
        participant2 = ChatParticipant(
            room_id=room.id,
            user_id=user2_id,
            is_active=True
        )
        
        self.db.add(participant1)
        self.db.add(participant2)
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_direct_room(self, user1_id: int, user2_id: int) -> Optional[ChatRoom]:
        """Get existing direct room between two users"""
        # Find rooms where both users are participants
        subquery = self.db.query(ChatParticipant.room_id).filter(
            and_(
                ChatParticipant.user_id.in_([user1_id, user2_id]),
                ChatParticipant.is_active == True
            )
        ).group_by(ChatParticipant.room_id).having(
            func.count(ChatParticipant.user_id) == 2
        ).subquery()
        
        return self.db.query(ChatRoom).filter(
            and_(
                ChatRoom.id.in_(subquery),
                ChatRoom.room_type == "direct",
                ChatRoom.is_active == True
            )
        ).first()

    def get_user_rooms(self, user_id: int) -> List[ChatRoom]:
        """Get all rooms for a user with last message info"""
        return self.db.query(ChatRoom).join(ChatParticipant).filter(
            and_(
                ChatParticipant.user_id == user_id,
                ChatRoom.is_active == True,
                ChatParticipant.is_active == True
            )
        ).order_by(desc(ChatRoom.updated_at), desc(ChatRoom.created_at)).all()

    def get_room(self, room_id: int, user_id: int) -> Optional[ChatRoom]:
        """Get a room if user is a participant"""
        return self.db.query(ChatRoom).join(ChatParticipant).filter(
            and_(
                ChatRoom.id == room_id,
                ChatParticipant.user_id == user_id,
                ChatRoom.is_active == True,
                ChatParticipant.is_active == True
            )
        ).first()

    def get_room_other_user(self, room_id: int, current_user_id: int) -> Optional[User]:
        """Get the other user in a direct chat room"""
        other_participant = self.db.query(ChatParticipant).join(User).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id != current_user_id,
                ChatParticipant.is_active == True
            )
        ).first()
        
        return other_participant.user if other_participant else None

    # Message Methods
    def create_message(self, room_id: int, sender_id: int, receiver_id: int, 
                      message_type: MessageType, content: str = None, 
                      file_name: str = None, file_path: str = None, 
                      file_size: int = None, mime_type: str = None,
                      files_data: list = None) -> ChatMessage:
        """Create a new message"""
        message = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            files_data=files_data
        )
        self.db.add(message)
        
        # Update room's updated_at timestamp
        room = self.db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if room:
            room.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        # Load sender relationship for immediate use
        self.db.refresh(message, ['sender'])
        return message

    def get_room_messages(self, room_id: int, user_id: int, page: int = 1, per_page: int = 50) -> List[ChatMessage]:
        """Get messages for a room with pagination"""
        # Verify user has access to the room
        if not self.get_room(room_id, user_id):
            return []
        
        offset = (page - 1) * per_page
        return self.db.query(ChatMessage).options(
            joinedload(ChatMessage.sender)
        ).filter(
            and_(
                ChatMessage.room_id == room_id,
                ChatMessage.is_deleted == False
            )
        ).order_by(desc(ChatMessage.created_at)).offset(offset).limit(per_page).all()
    
    def get_room_messages_count(self, room_id: int, user_id: int) -> int:
        """Get total count of messages in a room"""
        # Verify user has access to the room
        if not self.get_room(room_id, user_id):
            return 0
        
        return self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.room_id == room_id,
                ChatMessage.is_deleted == False
            )
        ).count()

    def get_last_message(self, room_id: int) -> Optional[ChatMessage]:
        """Get the last message in a room"""
        return self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.room_id == room_id,
                ChatMessage.is_deleted == False
            )
        ).order_by(desc(ChatMessage.created_at)).first()

    def mark_messages_as_read(self, room_id: int, user_id: int) -> bool:
        """Mark all messages in a room as read for a user"""
        # Update all unread messages from other users
        self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.room_id == room_id,
                ChatMessage.receiver_id == user_id,
                ChatMessage.is_read == False
            )
        ).update({"is_read": True})
        
        # Update participant's last_read_at
        participant = self.db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id
            )
        ).first()
        
        if participant:
            participant.last_read_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def get_unread_count(self, user_id: int) -> Dict[int, int]:
        """Get unread message count for each room"""
        unread_counts = {}
        rooms = self.get_user_rooms(user_id)
        
        for room in rooms:
            unread_count = self.db.query(ChatMessage).filter(
                and_(
                    ChatMessage.room_id == room.id,
                    ChatMessage.receiver_id == user_id,
                    ChatMessage.is_read == False,
                    ChatMessage.is_deleted == False
                )
            ).count()
            unread_counts[room.id] = unread_count
        
        return unread_counts

    def get_message(self, message_id: int) -> Optional[ChatMessage]:
        """Get a message by ID with sender and receiver info"""
        return self.db.query(ChatMessage).options(
            joinedload(ChatMessage.sender),
            joinedload(ChatMessage.receiver)
        ).filter(ChatMessage.id == message_id).first()

    def update_message(self, message_id: int, content: str, user_id: int) -> bool:
        """Update a message (only by sender, only text messages)"""
        message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id,
                ChatMessage.message_type == "text",
                ChatMessage.is_deleted == False
            )
        ).first()
        
        if message:
            message.content = content
            message.updated_at = datetime.utcnow()
            message.is_edited = True
            self.db.commit()
            return True
        return False

    def delete_message(self, message_id: int, user_id: int) -> bool:
        """Soft delete a message (only by sender)"""
        message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id
            )
        ).first()
        
        if message:
            message.is_deleted = True
            message.content = "This message was deleted"
            self.db.commit()
            return True
        return False

    # Presence Methods
    def update_user_presence(self, user_id: int, is_online: bool) -> UserPresence:
        """Update user's online status"""
        from datetime import timezone
        
        presence = self.db.query(UserPresence).filter(UserPresence.user_id == user_id).first()
        
        if not presence:
            presence = UserPresence(user_id=user_id)
            self.db.add(presence)
        
        presence.is_online = is_online
        presence.last_seen = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(presence)
        return presence

    def get_user_presence(self, user_id: int) -> Optional[UserPresence]:
        """Get user's presence status"""
        return self.db.query(UserPresence).filter(UserPresence.user_id == user_id).first()

    def get_online_users(self) -> List[UserPresence]:
        """Get all currently online users"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)
        
        return self.db.query(UserPresence).filter(
            and_(
                UserPresence.is_online == True,
                UserPresence.last_seen > five_minutes_ago
            )
        ).all()

    def is_user_online(self, user_id: int) -> bool:
        """Check if a user is currently online"""
        presence = self.get_user_presence(user_id)
        if not presence:
            return False
        
        # Consider user online if last seen within 5 minutes
        from datetime import timezone
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)
        return presence.is_online and presence.last_seen > five_minutes_ago

    # Message Like Methods
    def toggle_message_like(self, message_id: int, user_id: int) -> Dict[str, Any]:
        """Toggle like/unlike for a message. Returns {'action': 'liked'/'unliked', 'like_count': int}"""
        # Check if message exists and user has access to it
        message = self.db.query(ChatMessage).join(ChatRoom).join(ChatParticipant).filter(
            and_(
                ChatMessage.id == message_id,
                ChatParticipant.user_id == user_id,
                ChatMessage.is_deleted == False
            )
        ).first()
        
        if not message:
            return None
        
        # Check if user already liked this message
        existing_like = self.db.query(MessageLike).filter(
            and_(
                MessageLike.message_id == message_id,
                MessageLike.user_id == user_id
            )
        ).first()
        
        if existing_like:
            # Unlike: remove the like
            self.db.delete(existing_like)
            action = "unliked"
        else:
            # Like: add new like
            new_like = MessageLike(
                message_id=message_id,
                user_id=user_id
            )
            self.db.add(new_like)
            action = "liked"
        
        self.db.commit()
        
        # Get updated like count
        like_count = self.db.query(MessageLike).filter(
            MessageLike.message_id == message_id
        ).count()
        
        return {
            "action": action,
            "like_count": like_count
        }
    
    def is_message_liked_by_user(self, message_id: int, user_id: int) -> bool:
        """Check if a message is liked by a specific user"""
        like = self.db.query(MessageLike).filter(
            and_(
                MessageLike.message_id == message_id,
                MessageLike.user_id == user_id
            )
        ).first()
        return like is not None
    
    def get_message_like_count(self, message_id: int) -> int:
        """Get the total number of likes for a message"""
        return self.db.query(MessageLike).filter(
            MessageLike.message_id == message_id
        ).count()
