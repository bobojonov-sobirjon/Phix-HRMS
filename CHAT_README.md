# Real-Time Chat System for Phix HRMS

## Overview
This implementation adds a complete real-time chat system to your HRMS application with the following features:

- **User Search**: Search users by email to start conversations
- **Direct Messaging**: 1-on-1 chat between users
- **Real-time Communication**: WebSocket-based instant messaging
- **File Sharing**: Send images and files (not URLs)
- **Message Types**: Text, images, files, and voice messages
- **Online Status**: See who's online/offline
- **Message Read Status**: Track read/unread messages

## Database Tables Created

### 1. `chat_rooms`
- Stores chat room information
- Direct chat rooms between two users
- Room metadata and timestamps

### 2. `chat_participants`
- Manages who can access which chat rooms
- Tracks when users joined and last read messages

### 3. `chat_messages`
- Stores all messages (text, images, files)
- Includes sender/receiver information
- File metadata (name, path, size, MIME type)

### 4. `user_presence`
- Tracks user online/offline status
- Last seen timestamps

## API Endpoints

### User Search
- `GET /api/v1/chat/search-users?email={email}` - Search users by email

**Request:**
```http
GET /api/v1/chat/search-users?email=john@example.com
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "users": [
    {
      "id": 2,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
    }
  ],
  "total": 1
}
```

### Chat Rooms

#### Create Chat Room
- `POST /api/v1/chat/rooms` - Create a new chat room

**Request:**
```http
POST /api/v1/chat/rooms
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "receiver_id": 2
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Direct Chat",
  "room_type": "direct",
  "created_by": 1,
  "created_at": "2024-01-21T12:00:00Z",
  "updated_at": "2024-01-21T12:00:00Z",
  "is_active": true,
  "other_user": {
    "id": 2,
    "name": "John Doe",
    "email": "john@example.com",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_online": true
  },
  "last_message": null,
  "unread_count": 0
}
```

#### Get User Rooms
- `GET /api/v1/chat/rooms` - Get user's chat rooms

**Request:**
```http
GET /api/v1/chat/rooms
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "rooms": [
    {
      "id": 1,
      "name": "Direct Chat",
      "room_type": "direct",
      "created_by": 1,
      "created_at": "2024-01-21T12:00:00Z",
      "updated_at": "2024-01-21T12:05:00Z",
      "is_active": true,
      "other_user": {
        "id": 2,
        "name": "John Doe",
        "email": "john@example.com",
        "avatar_url": "https://example.com/avatar.jpg",
        "is_online": true
      },
      "last_message": {
        "id": 5,
        "content": "Hello there!",
        "message_type": "text",
        "created_at": "2024-01-21T12:05:00Z",
        "sender_name": "John Doe"
      },
      "unread_count": 2
    }
  ],
  "total": 1
}
```

#### Get Specific Room
- `GET /api/v1/chat/rooms/{room_id}` - Get specific room details with all messages

**Note:** This endpoint returns room information, last message summary, AND all messages in the room. Each message in `message_list` clearly shows who is the sender and who is the receiver.

**Request:**
```http
GET /api/v1/chat/rooms/1
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "id": 1,
  "name": "Direct Chat",
  "room_type": "direct",
  "created_by": 1,
  "created_at": "2024-01-21T12:00:00Z",
  "updated_at": "2024-01-21T12:05:00Z",
  "is_active": true,
  "other_user": {
    "id": 2,
    "name": "John Doe",
    "email": "john@example.com",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_online": true
  },
  "last_message": {
    "id": 5,
    "content": "Hello there!",
    "message_type": "text",
    "created_at": "2024-01-21T12:05:00Z",
    "sender_name": "John Doe"
  },
  "unread_count": 2,
  "message_list": {
    "messages": [
      {
        "id": 1,
        "room_id": 1,
        "sender_id": 1,
        "receiver_id": 2,
        "sender_name": "Alice Smith",
        "receiver_name": "John Doe",
        "sender_avatar": "https://example.com/alice.jpg",
        "receiver_avatar": "https://example.com/john.jpg",
        "message_type": "text",
        "content": "Hi John!",
        "file_name": null,
        "file_path": null,
        "file_size": null,
        "mime_type": null,
        "created_at": "2024-01-21T12:00:00Z",
        "is_read": true,
        "is_deleted": false
      },
      {
        "id": 2,
        "room_id": 1,
        "sender_id": 2,
        "receiver_id": 1,
        "sender_name": "John Doe",
        "receiver_name": "Alice Smith",
        "sender_avatar": "https://example.com/john.jpg",
        "receiver_avatar": "https://example.com/alice.jpg",
        "message_type": "text",
        "content": "Hello Alice!",
        "file_name": null,
        "file_path": null,
        "file_size": null,
        "mime_type": null,
        "created_at": "2024-01-21T12:01:00Z",
        "is_read": true,
        "is_deleted": false
      },
      {
        "id": 5,
        "room_id": 1,
        "sender_id": 2,
        "receiver_id": 1,
        "sender_name": "John Doe",
        "receiver_name": "Alice Smith",
        "sender_avatar": "https://example.com/john.jpg",
        "receiver_avatar": "https://example.com/alice.jpg",
        "message_type": "text",
        "content": "Hello there!",
        "file_name": null,
        "file_path": null,
        "file_size": null,
        "mime_type": null,
        "created_at": "2024-01-21T12:05:00Z",
        "is_read": false,
        "is_deleted": false
      }
    ],
    "total": 3
  }
}
```

**Message Structure in `message_list`:**
Each message object contains:
- **`sender_id`** & **`sender_name`** - Who sent the message
- **`receiver_id`** & **`receiver_name`** - Who received the message  
- **`sender_avatar`** & **`receiver_avatar`** - Profile pictures
- **`message_type`** - "text", "image", or "file"
- **`content`** - Message text (for text messages)
- **`file_name`**, **`file_path`**, **`file_size`**, **`mime_type`** - File details (for image/file messages)
- **`created_at`** - When the message was sent
- **`is_read`** - Whether the message has been read
- **`is_deleted`** - Whether the message has been deleted

**Example Message Flow:**
```json
// Message 1: Alice (ID: 1) sends to John (ID: 2)
{
  "sender_id": 1,
  "sender_name": "Alice Smith", 
  "receiver_id": 2,
  "receiver_name": "John Doe",
  "content": "Hi John!"
}

// Message 2: John (ID: 2) replies to Alice (ID: 1)  
{
  "sender_id": 2,
  "sender_name": "John Doe",
  "receiver_id": 1, 
  "receiver_name": "Alice Smith",
  "content": "Hello Alice!"
}
```

### Messages

**Important:** There are two different endpoints for getting room data:

1. **`GET /api/v1/chat/rooms/{room_id}`** - Room info + last message summary + ALL messages in one call
2. **`GET /api/v1/chat/rooms/{room_id}/messages`** - ALL messages in the room (with pagination)

Use the first one when opening a chat to get everything in one call. Use the second one for paginated message loading if you have many messages.

**Note:** All messages (text, image, file) are sent through WebSocket for real-time delivery. No separate REST API endpoints are needed for sending messages.

#### Get Room Messages
- `GET /api/v1/chat/rooms/{room_id}/messages` - Get ALL messages in a room (with pagination)

**Request:**
```http
GET /api/v1/chat/rooms/1/messages?page=1&per_page=50
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "messages": [
    {
      "id": 7,
      "room_id": 1,
      "sender_id": 1,
      "receiver_id": 2,
      "sender_name": "Alice Smith",
      "receiver_name": "John Doe",
      "sender_avatar": "https://example.com/alice.jpg",
      "receiver_avatar": "https://example.com/john.jpg",
      "message_type": "file",
      "content": null,
      "file_name": "document.pdf",
      "file_path": "chat_files/files/uuid-document.pdf",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "created_at": "2024-01-21T12:07:00Z",
      "is_read": false,
      "is_deleted": false
    },
    {
      "id": 6,
      "room_id": 1,
      "sender_id": 1,
      "receiver_id": 2,
      "sender_name": "Alice Smith",
      "receiver_name": "John Doe",
      "sender_avatar": "https://example.com/alice.jpg",
      "receiver_avatar": "https://example.com/john.jpg",
      "message_type": "image",
      "content": null,
      "file_name": "photo.jpg",
      "file_path": "chat_files/images/uuid-photo.jpg",
      "file_size": 245760,
      "mime_type": "image/jpeg",
      "created_at": "2024-01-21T12:06:00Z",
      "is_read": false,
      "is_deleted": false
    },
    {
      "id": 5,
      "room_id": 1,
      "sender_id": 1,
      "receiver_id": 2,
      "sender_name": "Alice Smith",
      "receiver_name": "John Doe",
      "sender_avatar": "https://example.com/alice.jpg",
      "receiver_avatar": "https://example.com/john.jpg",
      "message_type": "text",
      "content": "Hello there!",
      "file_name": null,
      "file_path": null,
      "file_size": null,
      "mime_type": null,
      "created_at": "2024-01-21T12:05:00Z",
      "is_read": false,
      "is_deleted": false
    }
  ],
  "total": 3,
  "has_more": false
}
```

#### Mark Room as Read
- `POST /api/v1/chat/rooms/{room_id}/read` - Mark room as read

**Request:**
```http
POST /api/v1/chat/rooms/1/read
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "status": "success",
  "message": "Room marked as read"
}
```

#### Update Message
- `PUT /api/v1/chat/messages/{message_id}` - Update message (only text messages)

**Request:**
```http
PUT /api/v1/chat/messages/5
Authorization: Bearer {jwt_token}
Content-Type: application/x-www-form-urlencoded

content=Updated message content
```

**Response:**
```json
{
  "id": 5,
  "room_id": 1,
  "sender_id": 1,
  "receiver_id": 2,
  "sender_name": "Alice Smith",
  "receiver_name": "John Doe",
  "sender_avatar": "https://example.com/alice.jpg",
  "receiver_avatar": "https://example.com/john.jpg",
  "message_type": "text",
  "content": "Updated message content",
  "file_name": null,
  "file_path": null,
  "file_size": null,
  "mime_type": null,
  "created_at": "2024-01-21T12:00:00Z",
  "updated_at": "2024-01-21T12:10:00Z",
  "is_read": false,
  "is_deleted": false,
  "is_edited": true
}
```

#### Delete Message
- `DELETE /api/v1/chat/messages/{message_id}` - Delete message

**Request:**
```http
DELETE /api/v1/chat/messages/5
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "status": "success",
  "message": "Message deleted"
}
```

### WebSocket
- `WS /api/v1/chat/ws?token={jwt_token}&room_id={room_id}` - Real-time chat connection (requires JWT token and optional room_id)

**Connection:**
```javascript
// Connect to specific room
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws?token=your-jwt-token&room_id=1');

// Or connect without room (join room later via message)
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws?token=your-jwt-token');
```

**Request:**
```http
WS /api/v1/chat/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
// Connection established - no initial response
// Server will start sending real-time messages

// If authentication fails, connection closes with error codes:
// 4000: General authentication error
// 4001: Missing/invalid token or user not found
```

**Connection States:**
- **Open**: Connection established successfully
- **Closed with 4000**: General authentication error
- **Closed with 4001**: Missing/invalid token or user not found
- **Closed with 1000**: Normal closure

**Complete WebSocket Flow:**
```json
// 1. Client connects with room_id in URL
WS /api/v1/chat/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&room_id=1

// 2. Server accepts connection and automatically joins room (no response)

// 3. Client sends a message (room_id is optional if provided in URL)
{
  "type": "send_message",
  "data": {
    "receiver_id": 2,
    "message_type": "text",
    "content": "Hello there!"
  }
}

// Alternative: Connect without room_id and join room via message
WS /api/v1/chat/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

// Then join room
{
  "type": "join_room",
  "data": {
    "room_id": 1
  }
}

// Then send message
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "text",
    "content": "Hello there!"
  }
}

// 5. Server broadcasts message to all users in room
{
  "type": "new_message",
  "data": {
    "id": 123,
    "room_id": 1,
    "sender_id": 1,
    "receiver_id": 2,
    "sender_name": "John Doe",
    "receiver_name": "Alice Smith",
    "message_type": "text",
    "content": "Hello there!",
    "created_at": "2024-01-21T12:00:00Z"
  }
}
```

**WebSocket Messages:** See the "WebSocket Events" section below for complete message formats.

### Utility Endpoints

#### Get Unread Count
- `GET /api/v1/chat/unread-count` - Get unread message counts

**Request:**
```http
GET /api/v1/chat/unread-count
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "unread_counts": {
    "1": 2,
    "3": 5,
    "7": 0
  }
}
```

#### Get Online Users
- `GET /api/v1/chat/online-users` - Get online users list

**Request:**
```http
GET /api/v1/chat/online-users
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "online_users": [
    {
      "user_id": 2,
      "last_seen": "2024-01-21T12:05:00Z",
      "is_online": true
    },
    {
      "user_id": 4,
      "last_seen": "2024-01-21T12:03:00Z",
      "is_online": true
    }
  ]
}
```

## File Upload System

### Supported File Types
**Images**: JPEG, JPG, PNG, GIF, WebP (max 10MB)
**Files**: PDF, DOC, DOCX, XLS, XLSX, TXT, ZIP, RAR (max 50MB)
**Voice**: MP3, WAV, M4A, AAC, OGG (max 20MB)

### File Storage
- Files stored in `static/chat_files/images/`, `static/chat_files/files/`, and `static/chat_files/voices/`
- Unique filenames generated using UUID
- Files accessible via `/static/chat_files/{type}/{filename}`

## WebSocket Events

### Client to Server Messages
```json
// Send text message (room_id optional if provided in URL)
{
  "type": "send_message",
  "data": {
    "receiver_id": 2,
    "message_type": "text",
    "content": "Hello there!"
  }
}

// Or with room_id in message (if not provided in URL)
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "text",
    "content": "Hello there!"
  }
}

// Send image message
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "image",
    "file_data": "base64_encoded_image_data",
    "file_name": "photo.jpg",
    "file_size": 245760,
    "mime_type": "image/jpeg"
  }
}

// Send file message
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "file",
    "file_data": "base64_encoded_file_data",
    "file_name": "document.pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf"
  }
}

// Send voice message
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "voice",
    "file_data": "base64_encoded_audio_data",
    "file_name": "voice_message.mp3",
    "file_size": 256000,
    "mime_type": "audio/mpeg"
  }
}

// Typing indicator
{
  "type": "typing",
  "data": {
    "room_id": 1,
    "is_typing": true
  }
}

// Join room
{
  "type": "join_room",
  "data": {
    "room_id": 1
  }
}

// Leave room
{
  "type": "leave_room",
  "data": {}
}
```

### Server to Client Messages
```json
// New message
{
  "type": "new_message",
  "data": {
    "id": 123,
    "room_id": 1,
    "sender_id": 1,
    "receiver_id": 2,
    "sender_name": "John Doe",
    "receiver_name": "Alice Smith",
    "sender_avatar": "https://example.com/john.jpg",
    "receiver_avatar": "https://example.com/alice.jpg",
    "message_type": "text",
    "content": "Hello!",
    "file_name": null,
    "file_path": null,
    "file_size": null,
    "mime_type": null,
    "created_at": "2024-01-21T12:00:00Z",
    "is_read": false,
    "is_deleted": false
  }
}

// Typing indicator
{
  "type": "typing",
  "data": {
    "room_id": 1,
    "user_id": 2,
    "user_name": "John Doe",
    "is_typing": true,
    "typing_users": [2]
  }
}

// User presence
{
  "type": "presence",
  "data": {
    "user_id": 2,
    "user_name": "John Doe",
    "is_online": true,
    "last_seen": "2024-01-21T12:05:00Z"
  }
}

// Message updated
{
  "type": "message_updated",
  "data": {
    "id": 123,
    "room_id": 1,
    "sender_id": 1,
    "receiver_id": 2,
    "sender_name": "John Doe",
    "receiver_name": "Alice Smith",
    "sender_avatar": "https://example.com/john.jpg",
    "receiver_avatar": "https://example.com/alice.jpg",
    "message_type": "text",
    "content": "Updated message content",
    "created_at": "2024-01-21T12:00:00Z",
    "updated_at": "2024-01-21T12:10:00Z",
    "is_edited": true
  }
}
```

## Usage Example

### 1. Search for a user
```http
GET /api/v1/chat/search-users?email=user@example.com
Authorization: Bearer your-token
```

### 2. Create a chat room
```http
POST /api/v1/chat/rooms
Authorization: Bearer your-token
Content-Type: application/json

{
  "receiver_id": 2
}
```

### 3. WebSocket Connection
```javascript
// Connect to specific room
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws?token=your-jwt-token&room_id=1');

// Or connect without room
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws?token=your-jwt-token');
```

## Testing

1. Start the server: `uvicorn app.main:app --reload`
2. **Login to get your JWT token** using your existing login API
3. Open `test_chat_client.html` in your browser
4. Enter the token in the test client and click "Update Token"
5. Use the test client to:
   - Search for users
   - Create chat rooms
   - Send messages and files
   - Test real-time communication

## Security Features

- JWT token authentication required for all endpoints and WebSocket connections
- WebSocket authentication via query parameter: `?token={jwt_token}`
- File type validation and size limits
- User can only access their own chat rooms
- Message deletion only by sender
- Secure file upload with proper validation
- WebSocket connection closes with error codes for authentication failures:
  - `4000`: General authentication error
  - `4001`: Missing/invalid token or user not found

## Performance Features

- Database connection pooling
- Efficient message pagination
- WebSocket connection management
- File size limits to prevent abuse
- Optimized database queries with proper indexing

## Next Steps

1. **Authentication**: Replace mock authentication with your actual JWT system
2. **File Cleanup**: Implement periodic cleanup of orphaned files
3. **Message Encryption**: Add end-to-end encryption for sensitive messages
4. **Push Notifications**: Integrate with mobile push notification services
5. **Message Search**: Add full-text search across messages
6. **Group Chats**: Extend to support group conversations
7. **Message Reactions**: Add emoji reactions to messages
8. **Voice Messages**: Support for audio file uploads

## Database Migration

The chat tables are automatically created when you start the application. If you need to run the migration manually:

```bash
alembic upgrade head
```

## File Structure

```
app/
├── models/chat.py              # Database models
├── schemas/chat.py             # Pydantic schemas
├── repositories/chat_repository.py  # Database operations
├── api/chat.py                 # API endpoints
└── utils/
    ├── websocket_manager.py    # WebSocket management
    └── file_upload.py          # File upload handling

static/chat_files/
├── images/                     # Uploaded images
└── files/                      # Uploaded files
```

This implementation provides a complete, production-ready chat system that integrates seamlessly with your existing HRMS application!
