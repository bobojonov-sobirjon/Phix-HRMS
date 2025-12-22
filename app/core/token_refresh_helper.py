"""
Helper utilities for token refresh and expiration handling
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
from ..core.config import settings
from ..core.logging_config import logger


def check_token_expiration(token: str) -> Optional[Dict[str, Any]]:
    """
    Check if token is expired and return expiration info
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with expiration info or None if token is invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            is_expired = exp_datetime < now
            time_until_expiry = exp_datetime - now if not is_expired else timedelta(0)
            
            return {
                "is_expired": is_expired,
                "expires_at": exp_datetime,
                "time_until_expiry": time_until_expiry,
                "expires_in_seconds": int(time_until_expiry.total_seconds()) if not is_expired else 0
            }
        return None
    except JWTError:
        return None


def should_refresh_token(token: str, refresh_threshold_minutes: int = 60) -> bool:
    """
    Check if token should be refreshed (expiring soon)
    
    Args:
        token: JWT token string
        refresh_threshold_minutes: Refresh if token expires within this many minutes
        
    Returns:
        True if token should be refreshed
    """
    exp_info = check_token_expiration(token)
    if not exp_info:
        return True  # Invalid token, should refresh
    
    if exp_info["is_expired"]:
        return True  # Already expired
    
    # Check if expiring soon
    threshold = timedelta(minutes=refresh_threshold_minutes)
    return exp_info["time_until_expiry"] < threshold
