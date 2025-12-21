"""
Common helper functions to reduce code duplication
"""
from typing import Optional, Dict, Any, List
from ..core.config import settings
from ..core.logging_config import logger


def build_file_url(file_path: Optional[str]) -> Optional[str]:
    """
    Build full URL for a file path
    
    Args:
        file_path: Relative file path
        
    Returns:
        Full URL or None if file_path is None
    """
    if not file_path:
        return None
    
    # Replace backslashes with forward slashes for web URLs
    clean_path = file_path.replace("\\", "/")
    return f"{settings.BASE_URL}/{clean_path}"


def build_files_data_with_urls(files_data: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """
    Build files data with full URLs
    
    Args:
        files_data: List of file data dictionaries
        
    Returns:
        List of file data with full URLs or None if files_data is None
    """
    if not files_data:
        return None
    
    files_data_with_urls = []
    for file_data in files_data:
        clean_path = file_data["file_path"].replace("\\", "/")
        file_data_with_url = {
            "file_name": file_data["file_name"],
            "file_path": build_file_url(file_data["file_path"]),
            "file_size": file_data["file_size"],
            "mime_type": file_data["mime_type"]
        }
        # Add duration for voice/audio messages
        if "duration" in file_data and file_data["duration"] is not None:
            file_data_with_url["duration"] = file_data["duration"]
        files_data_with_urls.append(file_data_with_url)
    
    return files_data_with_urls


def build_user_details(user, is_online: bool = False) -> Optional[Dict[str, Any]]:
    """
    Build user details dictionary
    
    Args:
        user: User model instance
        is_online: Whether user is online
        
    Returns:
        User details dictionary or None if user is None
    """
    if not user:
        return None
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_online": is_online
    }
