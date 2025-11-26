# Chat System Documentation

## Overview

The chat system provides real-time messaging capabilities with support for text messages, single files, and multiple files/images. It includes WebSocket-based real-time communication, file upload functionality, and user presence tracking.

## Features

### Core Features
- **Real-time messaging** via WebSocket connections
- **User search** by email
- **Direct chat rooms** between two users
- **Message types**: text, image, file, voice
- **Multiple file uploads** (up to 10 files per message)
- **File validation** with size and type restrictions
- **User presence** tracking (online/offline status)
- **Typing indicators**
- **Message read status**
- **Message editing** (text messages only)
- **Message deletion** (soft delete)

### File Upload Features
- **Multiple file upload** via `files_data` array
- **Image support**: JPEG, PNG, GIF, WebP
- **File support**: PDF, DOC, DOCX, XLS, XLSX, TXT, ZIP, RAR
- **Voice message support**: MP3, WAV
- **File size limits**: 10MB for images, 50MB for files and voice messages
- **Automatic file organization** by type

## API Endpoints

### Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### User Search
```http
GET /api/chat/search-users?email=user@example.com&limit=20
```
Search for users by email address.

**Response:**
```json
{
  "users": [
    {
      "id": 1,
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

#### Create Room
```http
POST /api/chat/rooms
Content-Type: application/json

{
  "receiver_id": 2
}
```

#### Get User Rooms
```http
GET /api/chat/rooms
```

#### Get Specific Room
```http
GET /api/chat/rooms/{room_id}
```

### File Upload

**Note:** All file uploads are handled through WebSocket connections for real-time delivery. No separate API endpoints are provided for file uploads.

### Messages

#### Get Room Messages
```http
GET /api/chat/rooms/{room_id}/messages?page=1&per_page=50
```

**Response:**
```json
{
  "messages": [
    {
      "id": 123,
      "content": "Hello!",
      "message_type": "text",
      "local_temp_id": null,  // Har doim bo'ladi (GET endpoint'da har doim null)
      "files_data": null,  // Har doim bo'ladi (file bo'lsa array, aks holda null)
      "created_at": "2024-01-01T12:00:00Z",
      "is_read": false,
      "is_deleted": false,
      "is_sender": true,
      "is_liked": false,
      "like_count": 0,
      "sender_details": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "avatar_url": "https://example.com/avatar.jpg",
        "is_online": true
      },
      "receiver_details": {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "avatar_url": "https://example.com/avatar2.jpg",
        "is_online": false
      }
    }
  ],
  "total": 100,
  "has_more": true,
  "page": 1,
  "per_page": 50,
  "total_pages": 2
}
```

**Important Notes:**
- `local_temp_id` har doim response'da bo'ladi (GET endpoint'da har doim `null`)
- `files_data` har doim response'da bo'ladi (file bo'lsa array, aks holda `null`)

#### Mark Messages as Read
```http
POST /api/chat/rooms/{room_id}/read
```

#### Update Message
```http
PUT /api/chat/messages/{message_id}
Content-Type: application/x-www-form-urlencoded

content=Updated message text
```

#### Delete Message
```http
DELETE /api/chat/messages/{message_id}
```

### Utility Endpoints

#### Get Unread Count
```http
GET /api/chat/unread-count
```

#### Get Online Users
```http
GET /api/chat/online-users
```

## WebSocket Connection

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/chat/ws?token=<jwt_token>&room_id=<room_id>');
```

### Message Types

#### Send Text Message
```json
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "text",
    "content": "Hello, how are you?"
  }
}
```

#### Send File Message (Single or Multiple)
Barcha file ma'lumotlari `files_data` array ichida yuboriladi. Bitta file bo'lsa ham array ichida bo'ladi.

**Request Structure:**
```json
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "image",
    "content": "Check out this image!",
    "local_temp_id": "temp_123",  // Optional: for client-side message matching
    "files_data": [
      {
        "file_data": "base64_encoded_file_data",
        "file_name": "photo1.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg",
        "duration": null  // Optional: for voice/audio messages (duration in seconds)
      }
    ]
  }
}
```

**Voice/Audio Message Example:**
```json
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "voice",
    "content": "Voice message",
    "local_temp_id": "temp_789",
    "files_data": [
      {
        "file_data": "base64_encoded_audio_data",
        "file_name": "voice_message.mp3",
        "file_size": 512000,
        "mime_type": "audio/mpeg",
        "duration": 30  // Duration in seconds (required for voice/audio messages)
      }
    ]
  }
}
```

**Multiple Files Example:**
```json
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "image",
    "content": "Here are some photos!",
    "local_temp_id": "temp_456",
    "files_data": [
      {
        "file_data": "base64_encoded_file1",
        "file_name": "photo1.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg",
        "duration": null  // Optional: for voice/audio messages (duration in seconds)
      },
      {
        "file_data": "base64_encoded_file2",
        "file_name": "photo2.jpg",
        "file_size": 2048000,
        "mime_type": "image/jpeg",
        "duration": null  // Optional: for voice/audio messages (duration in seconds)
      }
    ]
  }
}
```

**Important Notes:**
- Barcha file ma'lumotlari `files_data` array ichida bo'lishi kerak
- Bitta file bo'lsa ham array ichida yuboriladi
- `file_data`, `file_name`, `file_size`, `mime_type` alohida fieldlar sifatida yuborilmaydi
- `duration` - voice/audio message'lar uchun majburiy (sekundlarda)
- `local_temp_id` - ixtiyoriy, client-side message matching uchun

#### Typing Indicator
```json
{
  "type": "typing",
  "data": {
    "room_id": 1,
    "is_typing": true
  }
}
```

#### Join Room
```json
{
  "type": "join_room",
  "data": {
    "room_id": 1
  }
}
```

#### Leave Room
```json
{
  "type": "leave_room"
}
```

### WebSocket Responses

#### New Message Response
Barcha file ma'lumotlari `files_data` array ichida qaytariladi. `local_temp_id` va `files_data` har doim response'da bo'ladi.

**Text Message:**
```json
{
  "type": "new_message",
  "data": {
    "id": 123,
    "content": "Hello!",
    "message_type": "text",
    "local_temp_id": "temp_123",  // Har doim bo'ladi (request'da yuborilgan bo'lsa value, aks holda null)
    "files_data": null,  // Har doim bo'ladi (file bo'lsa array, aks holda null)
    "created_at": "2024-01-01T12:00:00Z",
    "is_read": false,
    "is_deleted": false,
    "sender_details": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
    },
    "receiver_details": {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "avatar_url": "https://example.com/avatar2.jpg",
      "is_online": false
    }
  }
}
```

**File Message (Single or Multiple):**
```json
{
  "type": "new_message",
  "data": {
    "id": 124,
    "content": "Here are some photos!",
    "message_type": "image",
    "local_temp_id": "temp_456",  // Har doim bo'ladi (request'da yuborilgan bo'lsa value, aks holda null)
    "files_data": [  // Har doim bo'ladi (file bo'lsa array, aks holda null)
      {
        "file_name": "photo1.jpg",
        "file_path": "https://api.example.com/static/chat_files/images/user_1_20240101_120000_0_photo1.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg",
        "duration": null  // Duration faqat voice/audio message'lar uchun (sekundlarda)
      },
      {
        "file_name": "photo2.jpg",
        "file_path": "https://api.example.com/static/chat_files/images/user_1_20240101_120000_1_photo2.jpg",
        "file_size": 2048000,
        "mime_type": "image/jpeg",
        "duration": null  // Duration faqat voice/audio message'lar uchun (sekundlarda)
      }
    ],
    "created_at": "2024-01-01T12:00:00Z",
    "is_read": false,
    "is_deleted": false,
    "sender_details": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
    },
    "receiver_details": {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "avatar_url": "https://example.com/avatar2.jpg",
      "is_online": false
    }
  }
}
```

**Voice/Audio Message Response:**
```json
{
  "type": "new_message",
  "data": {
    "id": 125,
    "content": "Voice message",
    "message_type": "voice",
    "local_temp_id": "temp_789",  // Har doim bo'ladi (request'da yuborilgan bo'lsa value, aks holda null)
    "files_data": [  // Har doim bo'ladi (file bo'lsa array, aks holda null)
      {
        "file_name": "voice_message.mp3",
        "file_path": "https://api.example.com/static/chat_files/voices/user_1_20240101_120000_0_voice_message.mp3",
        "file_size": 512000,
        "mime_type": "audio/mpeg",
        "duration": 30  // Duration in seconds (voice/audio messages uchun)
      }
    ],
    "duration": 30,  // Har doim bo'ladi (voice message bo'lsa value, aks holda null)
    "created_at": "2024-01-01T12:00:00Z",
    "is_read": false,
    "is_deleted": false,
    "sender_details": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
    },
    "receiver_details": {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "avatar_url": "https://example.com/avatar2.jpg",
      "is_online": false
    }
  }
}
```

**Important Notes:**
- `local_temp_id` har doim response'da bo'ladi (request'da yuborilgan bo'lsa value, aks holda `null`)
- `files_data` har doim response'da bo'ladi (file bo'lsa array, aks holda `null`)
- `duration` har doim response'da bo'ladi (voice message bo'lsa sekundlarda, aks holda `null`)
- Voice/audio message'lar uchun `duration` majburiy (sekundlarda)
- Barcha file ma'lumotlari `files_data` array ichida qaytariladi
- Bitta file bo'lsa ham array ichida bo'ladi
- `file_path` to'liq URL sifatida qaytariladi
- `files_data` ichidagi har bir file uchun ham `duration` bo'lishi mumkin (voice/audio uchun)

#### Typing Indicator
```json
{
  "type": "typing",
  "data": {
    "room_id": 1,
    "user_id": 1,
    "user_name": "John Doe",
    "is_typing": true
  }
}
```

#### User Presence
```json
{
  "type": "presence",
  "data": {
    "user_id": 1,
    "is_online": true,
    "user_name": "John Doe"
  }
}
```

#### Message Read
```json
{
  "type": "message_read",
  "data": {
    "room_id": 1,
    "user_id": 1,
    "user_name": "John Doe"
  }
}
```

#### Message Update
```json
{
  "type": "message_update",
  "data": {
    "id": 123,
    "content": "Updated message",
    "message_type": "text",
    "local_temp_id": null,  // Har doim bo'ladi (update endpoint'da har doim null)
    "files_data": null,  // Har doim bo'ladi (file bo'lsa array, aks holda null)
    "created_at": "2024-01-01T12:00:00Z",
    "is_read": false,
    "is_deleted": false,
    "sender_details": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
    },
    "receiver_details": {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "avatar_url": "https://example.com/avatar2.jpg",
      "is_online": false
    }
  }
}
```

#### Error Response
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Database Schema

### Chat Rooms
```sql
CREATE TABLE chat_rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    room_type VARCHAR(50) DEFAULT 'direct',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Chat Participants
```sql
CREATE TABLE chat_participants (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES chat_rooms(id),
    user_id INTEGER REFERENCES users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Chat Messages
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES chat_rooms(id),
    sender_id INTEGER REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    files_data JSON,  -- New field for multiple files
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### User Presence
```sql
CREATE TABLE user_presence (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## File Storage

### Directory Structure
```
static/
└── chat_files/
    ├── images/     # Image files (JPEG, PNG, GIF, WebP)
    ├── files/      # Document files (PDF, DOC, DOCX, etc.)
    └── voices/     # Voice messages (MP3, WAV)
```

### File Naming Convention
- **All files**: `{user_id}_{timestamp}_{index}_{original_filename}`
- Index starts from 0 for multiple files

### File Size Limits
- **Images**: 10MB maximum
- **Files**: 50MB maximum
- **Voice messages**: 50MB maximum

### Supported File Types

#### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

#### Documents
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Microsoft Excel (.xls, .xlsx)
- Plain Text (.txt)
- ZIP Archives (.zip)
- RAR Archives (.rar)

#### Voice Messages
- MP3 (.mp3)
- WAV (.wav)

## Implementation Examples

### Frontend JavaScript Example

#### WebSocket Connection
```javascript
class ChatClient {
    constructor(token, roomId) {
        this.token = token;
        this.roomId = roomId;
        this.ws = null;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(`ws://localhost:8000/api/chat/ws?token=${this.token}&room_id=${this.roomId}`);
        
        this.ws.onopen = () => {
            console.log('Connected to chat');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from chat');
            // Reconnect logic here
        };
    }

    handleMessage(data) {
        switch(data.type) {
            case 'new_message':
                this.displayMessage(data.data);
                break;
            case 'typing':
                this.showTypingIndicator(data.data);
                break;
            case 'presence':
                this.updateUserPresence(data.data);
                break;
            case 'error':
                this.showError(data.message);
                break;
        }
    }

    sendTextMessage(content, receiverId) {
        const message = {
            type: 'send_message',
            data: {
                room_id: this.roomId,
                receiver_id: receiverId,
                message_type: 'text',
                content: content
            }
        };
        this.ws.send(JSON.stringify(message));
    }

    sendFiles(files, receiverId, messageType = 'image', content = '', localTempId = null) {
        // Send single or multiple files - all files in files_data array
        const filesData = [];
        let processedCount = 0;
        
        if (files.length === 0) return;
        
        files.forEach((file, index) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                // Remove data:image/jpeg;base64, prefix if present
                const base64Data = e.target.result.includes(',') 
                    ? e.target.result.split(',')[1] 
                    : e.target.result;
                
                filesData[index] = {
                    file_data: base64Data,
                    file_name: file.name,
                    file_size: file.size,
                    mime_type: file.type
                };
                
                processedCount++;
                
                // Send message when all files are processed
                if (processedCount === files.length) {
                    const message = {
                        type: 'send_message',
                        data: {
                            room_id: this.roomId,
                            receiver_id: receiverId,
                            message_type: messageType,
                            content: content || `Sent ${files.length} file${files.length > 1 ? 's' : ''}`,
                            local_temp_id: localTempId,
                            files_data: filesData
                        }
                    };
                    this.ws.send(JSON.stringify(message));
                }
            };
            
            reader.onerror = () => {
                console.error('Error reading file:', file.name);
            };
            
            reader.readAsDataURL(file);
        });
    }

    sendTypingIndicator(isTyping) {
        const message = {
            type: 'typing',
            data: {
                room_id: this.roomId,
                is_typing: isTyping
            }
        };
        this.ws.send(JSON.stringify(message));
    }
}
```

#### File Upload via WebSocket
```javascript
// All file uploads are handled directly through WebSocket
// No separate API calls needed for file uploads
```

### React Component Example

```jsx
import React, { useState, useEffect, useRef } from 'react';

const ChatRoom = ({ roomId, token, receiverId }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const wsRef = useRef(null);

    useEffect(() => {
        // Initialize WebSocket connection
        wsRef.current = new WebSocket(`ws://localhost:8000/api/chat/ws?token=${token}&room_id=${roomId}`);
        
        wsRef.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };

        return () => {
            wsRef.current?.close();
        };
    }, [roomId, token]);

    const handleWebSocketMessage = (data) => {
        switch(data.type) {
            case 'new_message':
                setMessages(prev => [...prev, data.data]);
                break;
            case 'typing':
                setIsTyping(data.data.is_typing);
                break;
        }
    };

    const sendMessage = () => {
        if (newMessage.trim()) {
            wsRef.current.send(JSON.stringify({
                type: 'send_message',
                data: {
                    room_id: roomId,
                    receiver_id: receiverId,
                    message_type: 'text',
                    content: newMessage
                }
            }));
            setNewMessage('');
        }
    };

    const sendFiles = () => {
        if (selectedFiles.length === 0) return;

        // Convert files to base64 and send via WebSocket
        // All files must be in files_data array (single or multiple)
        const filesData = [];
        let processedCount = 0;
        const localTempId = `temp_${Date.now()}`; // Generate temp ID for client-side matching

        selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Remove data:image/jpeg;base64, prefix if present
                const base64Data = e.target.result.includes(',') 
                    ? e.target.result.split(',')[1] 
                    : e.target.result;
                
                filesData[index] = {
                    file_data: base64Data,
                    file_name: file.name,
                    file_size: file.size,
                    mime_type: file.type
                };
                processedCount++;

                // Send when all files are processed
                if (processedCount === selectedFiles.length) {
                    // Determine message type based on first file
                    const messageType = file.type.startsWith('image/') ? 'image' 
                        : file.type.startsWith('audio/') ? 'voice' 
                        : 'file';
                    
                    wsRef.current.send(JSON.stringify({
                        type: 'send_message',
                        data: {
                            room_id: roomId,
                            receiver_id: receiverId,
                            message_type: messageType,
                            content: `Sent ${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''}`,
                            local_temp_id: localTempId,
                            files_data: filesData
                        }
                    }));
                    
                    setSelectedFiles([]);
                }
            };
            
            reader.onerror = () => {
                console.error('Error reading file:', file.name);
            };
            
            reader.readAsDataURL(file);
        });
    };

    const handleFileSelect = (event) => {
        const files = Array.from(event.target.files);
        setSelectedFiles(prev => [...prev, ...files]);
    };

    return (
        <div className="chat-room">
            <div className="messages">
                {messages.map(message => (
                    <div key={message.id} className={`message ${message.is_sender ? 'sent' : 'received'}`}>
                        <div className="message-content">
                            {message.content && <p>{message.content}</p>}
                            
                            {/* Files display - all files in files_data array */}
                            {message.files_data && message.files_data.length > 0 && (
                                <div className="files-container">
                                    {message.files_data.map((file, index) => (
                                        <div key={index} className="file-attachment">
                                            {file.mime_type?.startsWith('image/') ? (
                                                <img 
                                                    src={file.file_path} 
                                                    alt={file.file_name}
                                                    style={{ maxWidth: '200px', maxHeight: '200px' }}
                                                />
                                            ) : (
                                                <a href={file.file_path} target="_blank" rel="noopener noreferrer">
                                                    📎 {file.file_name} ({(file.file_size / 1024).toFixed(2)} KB)
                                                </a>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="message-meta">
                            <span className="sender">{message.sender_details?.name}</span>
                            <span className="timestamp">{new Date(message.created_at).toLocaleTimeString()}</span>
                        </div>
                    </div>
                ))}
                
                {isTyping && (
                    <div className="typing-indicator">
                        <span>Someone is typing...</span>
                    </div>
                )}
            </div>
            
            <div className="message-input">
                <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type a message..."
                />
                
                <input
                    type="file"
                    multiple
                    accept="image/*,.pdf,.doc,.docx,.txt,.zip,.rar"
                    onChange={handleFileSelect}
                />
                
                {selectedFiles.length > 0 && (
                    <div className="selected-files">
                        <p>Selected files: {selectedFiles.length}</p>
                        <button onClick={sendFiles}>Send Files</button>
                        <button onClick={() => setSelectedFiles([])}>Clear</button>
                    </div>
                )}
                
                <button onClick={sendMessage}>Send</button>
            </div>
        </div>
    );
};

export default ChatRoom;
```

## Error Handling

### Common Error Responses

#### Authentication Error
```json
{
  "detail": "Not authenticated"
}
```

#### File Upload Error
```json
{
  "detail": "File too large. Maximum size: 10.0MB"
}
```

#### Invalid File Type
```json
{
  "detail": "File type not allowed. Allowed types: image/jpeg, image/png, image/gif, image/webp"
}
```

#### Room Not Found
```json
{
  "detail": "Room not found"
}
```

#### Message Not Found
```json
{
  "detail": "Message not found"
}
```

## Security Considerations

1. **File Validation**: All uploaded files are validated for type and size
2. **Authentication**: All endpoints require valid JWT tokens
3. **File Storage**: Files are stored in a secure directory structure
4. **SQL Injection**: All database queries use parameterized statements
5. **XSS Prevention**: File names are sanitized before storage

## Performance Considerations

1. **File Size Limits**: Enforced to prevent storage issues
2. **Multiple File Limit**: Maximum 10 files per upload
3. **Database Indexing**: Proper indexes on frequently queried columns
4. **WebSocket Connection Management**: Efficient connection pooling
5. **File Cleanup**: Old files can be cleaned up periodically

## Deployment Notes

1. **Database Migration**: Run `alembic upgrade head` to apply schema changes
2. **Static Files**: Ensure static file serving is configured
3. **WebSocket Support**: Configure reverse proxy for WebSocket connections
4. **File Storage**: Ensure sufficient disk space for file uploads
5. **Environment Variables**: Configure BASE_URL and other settings

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check JWT token validity
   - Verify WebSocket URL format
   - Check network connectivity

2. **File Upload Failed**
   - Verify file size limits
   - Check file type restrictions
   - Ensure proper permissions on upload directory

3. **Messages Not Appearing**
   - Check WebSocket connection status
   - Verify room_id and receiver_id
   - Check authentication token

4. **Database Errors**
   - Run database migrations
   - Check database connection
   - Verify table schemas

### Debug Mode

Enable debug logging by setting the appropriate log level in your application configuration.

## API Rate Limits

- **File Upload**: 10 files per request
- **Message Size**: 5000 characters maximum
- **WebSocket Messages**: No specific rate limit (handled by WebSocket connection limits)

## Future Enhancements

1. **Group Chat Support**: Multi-user chat rooms
2. **File Compression**: Automatic image compression
3. **Message Reactions**: Emoji reactions to messages
4. **Message Forwarding**: Forward messages to other users
5. **Message Search**: Search within chat history
6. **Voice/Video Calls**: Integration with Agora or similar services
7. **Message Encryption**: End-to-end encryption for sensitive messages
8. **File Sharing**: Temporary file sharing links
9. **Message Scheduling**: Schedule messages for later delivery
10. **Chat Backup**: Export chat history

---

For more information or support, please contact the development team.