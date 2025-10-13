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
- **Single file upload** (backward compatibility)
- **Multiple file upload** (new feature)
- **Image support**: JPEG, PNG, GIF, WebP
- **File support**: PDF, DOC, DOCX, XLS, XLSX, TXT, ZIP, RAR
- **Voice message support**: MP3, WAV
- **File size limits**: 10MB for images, 50MB for files
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

#### Multiple File Upload
```http
POST /api/chat/upload-files
Content-Type: multipart/form-data

files: [file1, file2, file3, ...]
message_type: "image" | "file"
```

**Response:**
```json
{
  "files": [
    {
      "file_name": "image1.jpg",
      "file_path": "chat_files/images/uuid_image1.jpg",
      "file_size": 1024000,
      "mime_type": "image/jpeg"
    }
  ],
  "total_files": 3,
  "total_size": 3072000
}
```

### Messages

#### Get Room Messages
```http
GET /api/chat/rooms/{room_id}/messages?page=1&per_page=50
```

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

#### Send Single File Message
```json
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "image",
    "content": "Check out this image!",
    "file_data": "base64_encoded_file_data",
    "file_name": "image.jpg",
    "file_size": 1024000,
    "mime_type": "image/jpeg"
  }
}
```

#### Send Multiple Files Message
```json
{
  "type": "send_message",
  "data": {
    "room_id": 1,
    "receiver_id": 2,
    "message_type": "image",
    "content": "Here are some photos!",
    "files_data": [
      {
        "file_data": "base64_encoded_file1",
        "file_name": "photo1.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg"
      },
      {
        "file_data": "base64_encoded_file2",
        "file_name": "photo2.jpg",
        "file_size": 2048000,
        "mime_type": "image/jpeg"
      }
    ]
  }
}
```

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

#### New Message
```json
{
  "type": "new_message",
  "data": {
    "id": 123,
    "content": "Hello!",
    "message_type": "text",
    "file_name": null,
    "file_path": null,
    "file_size": null,
    "files_data": null,
    "created_at": "2024-01-01T12:00:00Z",
    "is_read": false,
    "is_deleted": false,
    "sender_details": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
    }
  }
}
```

#### Multiple Files Message
```json
{
  "type": "new_message",
  "data": {
    "id": 124,
    "content": "Here are some photos!",
    "message_type": "image",
    "file_name": null,
    "file_path": null,
    "file_size": null,
    "files_data": [
      {
        "file_name": "photo1.jpg",
        "file_path": "http://localhost:8000/static/chat_files/images/uuid_photo1.jpg",
        "file_size": 1024000,
        "mime_type": "image/jpeg"
      },
      {
        "file_name": "photo2.jpg",
        "file_path": "http://localhost:8000/static/chat_files/images/uuid_photo2.jpg",
        "file_size": 2048000,
        "mime_type": "image/jpeg"
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
    }
  }
}
```

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
    "file_name": null,
    "file_path": null,
    "file_size": null,
    "files_data": null,
    "created_at": "2024-01-01T12:00:00Z",
    "is_read": false,
    "is_deleted": false,
    "sender_details": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_online": true
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
- **Single files**: `{user_id}_{timestamp}_{original_filename}`
- **Multiple files**: `{user_id}_{timestamp}_{index}_{original_filename}`

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

    sendMultipleFiles(files, receiverId, messageType = 'image') {
        const filesData = [];
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const reader = new FileReader();
            
            reader.onload = (e) => {
                filesData.push({
                    file_data: e.target.result.split(',')[1], // Remove data:image/jpeg;base64, prefix
                    file_name: file.name,
                    file_size: file.size,
                    mime_type: file.type
                });

                // Send message when all files are processed
                if (filesData.length === files.length) {
                    const message = {
                        type: 'send_message',
                        data: {
                            room_id: this.roomId,
                            receiver_id: receiverId,
                            message_type: messageType,
                            content: `Sent ${files.length} files`,
                            files_data: filesData
                        }
                    };
                    this.ws.send(JSON.stringify(message));
                }
            };
            
            reader.readAsDataURL(file);
        }
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

#### File Upload with Progress
```javascript
async function uploadMultipleFiles(files, messageType) {
    const formData = new FormData();
    
    for (let file of files) {
        formData.append('files', file);
    }
    formData.append('message_type', messageType);

    try {
        const response = await fetch('/api/chat/upload-files', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log('Files uploaded:', result);
            return result.files;
        } else {
            throw new Error(result.detail || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}
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

    const sendMultipleFiles = async () => {
        if (selectedFiles.length === 0) return;

        try {
            const files = await uploadMultipleFiles(selectedFiles, 'image');
            
            wsRef.current.send(JSON.stringify({
                type: 'send_message',
                data: {
                    room_id: roomId,
                    receiver_id: receiverId,
                    message_type: 'image',
                    content: `Sent ${files.length} files`,
                    files_data: files.map(file => ({
                        file_data: file.file_path, // This would need to be base64 encoded
                        file_name: file.file_name,
                        file_size: file.file_size,
                        mime_type: file.mime_type
                    }))
                }
            }));
            
            setSelectedFiles([]);
        } catch (error) {
            console.error('Failed to send files:', error);
        }
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
                            
                            {/* Single file display */}
                            {message.file_path && (
                                <div className="file-attachment">
                                    <a href={message.file_path} target="_blank" rel="noopener noreferrer">
                                        {message.file_name}
                                    </a>
                                </div>
                            )}
                            
                            {/* Multiple files display */}
                            {message.files_data && message.files_data.length > 0 && (
                                <div className="multiple-files">
                                    {message.files_data.map((file, index) => (
                                        <div key={index} className="file-attachment">
                                            <a href={file.file_path} target="_blank" rel="noopener noreferrer">
                                                {file.file_name}
                                            </a>
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
                        <button onClick={sendMultipleFiles}>Send Files</button>
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