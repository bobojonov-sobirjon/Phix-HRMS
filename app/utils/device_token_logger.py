"""
Device Token Logging Utility
Handles creation of user device tokens with proper logging
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from ..models.user_device_token import UserDeviceToken, DeviceType

# Configure logger
logger = logging.getLogger(__name__)


def create_user_device_token(
    db: Session,
    user_id: int,
    device_token: Optional[str] = None,
    device_type: Optional[str] = None
) -> Optional[UserDeviceToken]:
    """
    Create or update user device token with logging.
    If a device token already exists for the same user_id and device_type, it will be updated.
    Otherwise, a new device token will be created.
    
    Args:
        db: Database session
        user_id: User ID to associate device token with
        device_token: Device token string (optional)
        device_type: Device type - "ios" or "android" (optional)
    
    Returns:
        UserDeviceToken object if created/updated successfully, None otherwise
    """
    # Check if both device_token and device_type are provided
    if not device_token or not device_type:
        logger.info(f"Device token not created for user {user_id}: missing device_token or device_type")
        return None
    
    # Validate device_type
    if device_type not in ['ios', 'android']:
        logger.warning(f"Invalid device_type '{device_type}' for user {user_id}. Must be 'ios' or 'android'")
        return None
    
    try:
        # Check if device token already exists for this user and device type (regardless of is_active status)
        existing_token = db.query(UserDeviceToken).filter(
            UserDeviceToken.user_id == user_id,
            UserDeviceToken.device_type == DeviceType(device_type)
        ).first()
        
        if existing_token:
            # Update existing device token
            existing_token.device_token = device_token
            existing_token.is_active = True
            db.commit()
            db.refresh(existing_token)
            
            logger.info(f"Device token updated for user {user_id}, device_type: {device_type}")
            return existing_token
        else:
            # Create new device token
            device_token_obj = UserDeviceToken(
                user_id=user_id,
                device_token=device_token,
                device_type=DeviceType(device_type),
                is_active=True
            )
            db.add(device_token_obj)
            db.commit()
            db.refresh(device_token_obj)
            
            logger.info(f"Device token created successfully for user {user_id}, device_type: {device_type}")
            return device_token_obj
        
    except Exception as e:
        logger.error(f"Error creating/updating device token for user {user_id}: {str(e)}")
        db.rollback()
        # Don't fail registration if device token creation fails
        return None

