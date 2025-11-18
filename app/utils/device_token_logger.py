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
        print(f"[DeviceToken] Device token not created for user {user_id}: missing device_token or device_type")
        return None
    
    # Validate device_type
    if device_type not in ['ios', 'android']:
        logger.warning(f"Invalid device_type '{device_type}' for user {user_id}. Must be 'ios' or 'android'")
        print(f"[DeviceToken] Invalid device_type '{device_type}' for user {user_id}")
        return None
    
    try:
        # Normalize device_type to lowercase for enum conversion
        device_type_lower = device_type.lower()
        
        # Convert device_type string to DeviceType enum using the value (not the name)
        # DeviceType.ANDROID.value = "android", DeviceType.IOS.value = "ios"
        if device_type_lower == "android":
            device_type_enum = DeviceType.ANDROID
        elif device_type_lower == "ios":
            device_type_enum = DeviceType.IOS
        else:
            raise ValueError(f"Invalid device_type: {device_type}")
        
        # Check if device token already exists for this user and device type (regardless of is_active status)
        existing_token = db.query(UserDeviceToken).filter(
            UserDeviceToken.user_id == user_id,
            UserDeviceToken.device_type == device_type_enum
        ).first()
        
        if existing_token:
            # Update existing device token
            print(f"[DeviceToken] Found existing token (id={existing_token.id}) for user {user_id}, updating...")
            existing_token.device_token = device_token
            existing_token.is_active = True
            db.flush()
            db.commit()
            db.refresh(existing_token)
            
            logger.info(f"Device token updated for user {user_id}, device_type: {device_type}")
            print(f"[DeviceToken] Device token updated successfully for user {user_id}, device_type: {device_type}, token_id: {existing_token.id}")
            return existing_token
        else:
            # Create new device token
            print(f"[DeviceToken] No existing token found for user {user_id}, creating new one...")
            device_token_obj = UserDeviceToken(
                user_id=user_id,
                device_token=device_token,
                device_type=device_type_enum,
                is_active=True
            )
            db.add(device_token_obj)
            db.flush()
            db.commit()
            db.refresh(device_token_obj)
            
            logger.info(f"Device token created successfully for user {user_id}, device_type: {device_type}")
            print(f"[DeviceToken] Device token created successfully for user {user_id}, device_type: {device_type}, token_id: {device_token_obj.id}")
            return device_token_obj
        
    except ValueError as ve:
        error_msg = f"Invalid device_type value '{device_type}' for user {user_id}: {str(ve)}"
        logger.error(error_msg)
        print(f"[DeviceToken] ERROR: {error_msg}")
        db.rollback()
        return None
    except Exception as e:
        error_msg = f"Error creating/updating device token for user {user_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"[DeviceToken] ERROR: {error_msg}")
        import traceback
        print(f"[DeviceToken] Traceback: {traceback.format_exc()}")
        db.rollback()
        # Don't fail registration if device token creation fails
        return None

