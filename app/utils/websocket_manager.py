from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, WebSocket] = {}
        # Store user's current room
        self.user_rooms: Dict[int, int] = {}
        # Store typing indicators by room
        self.typing_users: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Store a WebSocket connection (websocket should already be accepted)"""
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected")

    def disconnect(self, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_rooms:
            del self.user_rooms[user_id]
        # Remove from typing indicators
        for room_id, typing_set in self.typing_users.items():
            typing_set.discard(user_id)
        print(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def send_to_room_participants(self, message: dict, room_id: int, exclude_user: int = None):
        """Send a message to all users in a specific room"""
        # This would need room participant data from database
        # For now, we'll send to all connected users
        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending room message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def send_direct_message(self, message: dict, sender_id: int, receiver_id: int):
        """Send a direct message to a specific receiver"""
        # Send to receiver
        if receiver_id in self.active_connections:
            try:
                await self.active_connections[receiver_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending direct message to user {receiver_id}: {e}")
                self.disconnect(receiver_id)
        
        # Send back to sender for confirmation
        if sender_id in self.active_connections:
            try:
                await self.active_connections[sender_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending confirmation to sender {sender_id}: {e}")
                self.disconnect(sender_id)

    async def broadcast_typing(self, room_id: int, user_id: int, is_typing: bool, user_name: str):
        """Broadcast typing indicator to room participants"""
        if is_typing:
            if room_id not in self.typing_users:
                self.typing_users[room_id] = set()
            self.typing_users[room_id].add(user_id)
        else:
            if room_id in self.typing_users:
                self.typing_users[room_id].discard(user_id)

        # Send typing indicator to all users in the room
        typing_message = {
            "type": "typing",
            "data": {
                "room_id": room_id,
                "user_id": user_id,
                "user_name": user_name,
                "is_typing": is_typing,
                "typing_users": list(self.typing_users.get(room_id, set()))
            }
        }
        
        await self.send_to_room_participants(typing_message, room_id, exclude_user=user_id)

    async def broadcast_presence(self, user_id: int, is_online: bool, user_name: str = None):
        """Broadcast user presence update to all connected users"""
        presence_message = {
            "type": "presence",
            "data": {
                "user_id": user_id,
                "user_name": user_name,
                "is_online": is_online,
                "last_seen": datetime.utcnow().isoformat()
            }
        }
        
        # Send to all connected users except the user themselves
        for uid, websocket in self.active_connections.items():
            if uid != user_id:
                try:
                    await websocket.send_text(json.dumps(presence_message))
                except Exception as e:
                    print(f"Error broadcasting presence to user {uid}: {e}")
                    self.disconnect(uid)

    async def broadcast_new_message(self, message_data: dict, room_id: int, sender_id: int, receiver_id: int):
        """Broadcast new message to room participants"""
        # Send to sender (is_sender: true - o'ng tomonda)
        sender_message = {
            "type": "new_message",
            "data": {**message_data, "is_sender": True}
        }
        
        # Send to receiver (is_sender: false - chap tomonda)
        receiver_message = {
            "type": "new_message", 
            "data": {**message_data, "is_sender": False}
        }
        
        # Send to sender
        if sender_id in self.active_connections:
            try:
                await self.active_connections[sender_id].send_text(json.dumps(sender_message))
            except Exception as e:
                print(f"Error sending message to sender {sender_id}: {e}")
                self.disconnect(sender_id)
        
        # Send to receiver
        if receiver_id in self.active_connections:
            try:
                await self.active_connections[receiver_id].send_text(json.dumps(receiver_message))
            except Exception as e:
                print(f"Error sending message to receiver {receiver_id}: {e}")
                self.disconnect(receiver_id)

    async def broadcast_message_read(self, room_id: int, user_id: int, user_name: str):
        """Broadcast message read status"""
        read_message = {
            "type": "message_read",
            "data": {
                "room_id": room_id,
                "user_id": user_id,
                "user_name": user_name,
                "read_at": datetime.utcnow().isoformat()
            }
        }
        
        await self.send_to_room_participants(read_message, room_id, exclude_user=user_id)

    async def broadcast_message_update(self, message_data: dict, room_id: int, sender_id: int, receiver_id: int):
        """Broadcast message update to room participants"""
        message = {
            "type": "message_updated",
            "data": message_data
        }
        
        await self.send_direct_message(message, sender_id, receiver_id)

    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())

    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.active_connections

    def get_user_room(self, user_id: int) -> int:
        """Get user's current room"""
        return self.user_rooms.get(user_id)

    def set_user_room(self, user_id: int, room_id: int):
        """Set user's current room"""
        self.user_rooms[user_id] = room_id

    def leave_room(self, user_id: int):
        """Remove user from current room"""
        if user_id in self.user_rooms:
            del self.user_rooms[user_id]

    # Video Calling Methods
    async def broadcast_video_call(self, call_id: str, channel_name: str, caller_id: int, caller_name: str, receiver_id: int, room_id: int):
        """Broadcast video call notification"""
        call_message = {
            "type": "video_call",
            "data": {
                "call_id": call_id,
                "channel_name": channel_name,
                "caller_id": caller_id,
                "caller_name": caller_name,
                "receiver_id": receiver_id,
                "room_id": room_id,
                "status": "calling",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        # Send to receiver
        if receiver_id in self.active_connections:
            try:
                await self.active_connections[receiver_id].send_text(json.dumps(call_message))
            except Exception as e:
                print(f"Error sending video call to receiver {receiver_id}: {e}")
                self.disconnect(receiver_id)
        
        # Send confirmation to caller
        if caller_id in self.active_connections:
            try:
                await self.active_connections[caller_id].send_text(json.dumps(call_message))
            except Exception as e:
                print(f"Error sending video call confirmation to caller {caller_id}: {e}")
                self.disconnect(caller_id)

    async def broadcast_video_call_answer(self, call_id: str, receiver_id: int, receiver_name: str):
        """Broadcast video call answered notification"""
        answer_message = {
            "type": "video_call_answered",
            "data": {
                "call_id": call_id,
                "receiver_id": receiver_id,
                "receiver_name": receiver_name,
                "status": "answered",
                "answered_at": datetime.utcnow().isoformat()
            }
        }
        
        # Send to all connected users (both caller and receiver will receive this)
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(answer_message))
            except Exception as e:
                print(f"Error broadcasting video call answer to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_video_call_reject(self, call_id: str, receiver_id: int, receiver_name: str):
        """Broadcast video call rejected notification"""
        reject_message = {
            "type": "video_call_rejected",
            "data": {
                "call_id": call_id,
                "receiver_id": receiver_id,
                "receiver_name": receiver_name,
                "status": "rejected",
                "rejected_at": datetime.utcnow().isoformat()
            }
        }
        
        # Send to all connected users
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(reject_message))
            except Exception as e:
                print(f"Error broadcasting video call rejection to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_video_call_end(self, call_id: str, user_id: int, user_name: str):
        """Broadcast video call ended notification"""
        end_message = {
            "type": "video_call_ended",
            "data": {
                "call_id": call_id,
                "user_id": user_id,
                "user_name": user_name,
                "status": "ended",
                "ended_at": datetime.utcnow().isoformat()
            }
        }
        
        # Send to all connected users
        for uid, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(end_message))
            except Exception as e:
                print(f"Error broadcasting video call end to user {uid}: {e}")
                self.disconnect(uid)

# Global connection manager instance
manager = ConnectionManager()
