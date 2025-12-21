from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from ..db.database import SessionLocal
from ..models.user import User
from ..utils.auth import verify_token
from typing import Optional

async def authenticate_websocket(websocket: WebSocket) -> Optional[User]:
    """Authenticate WebSocket connection using token from query parameters"""
    try:
        # Get token from query parameters
        query_params = websocket.query_params
        token = query_params.get("token")
        
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return None
        
        # Verify the token
        try:
            payload = verify_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Invalid or expired token")
                return None
                
            # Check token type
            token_type = payload.get("type")
            if token_type != "access":
                await websocket.close(code=4001, reason="Invalid token type")
                return None
                
            user_id = payload.get("sub") or payload.get("user_id")
            
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token payload - no user_id")
                return None
            
            # Get user from database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if not user:
                    await websocket.close(code=4001, reason="User not found")
                    return None
                
                if not user.is_active:
                    await websocket.close(code=4001, reason="User account is inactive")
                    return None
                
                return user
            finally:
                db.close()
                
        except Exception as e:
            await websocket.close(code=4001, reason=f"Token verification failed: {str(e)}")
            return None
            
    except Exception as e:
        await websocket.close(code=4000, reason=f"Authentication error: {str(e)}")
        return None
