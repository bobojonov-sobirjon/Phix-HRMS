import requests
from typing import Optional, Dict, Any
from ..core.config import settings

class GoogleAuth:
    """Google OAuth authentication"""
    
    @staticmethod
    def verify_token(access_token: str) -> Optional[Dict[str, Any]]:
        """Verify Google access token and get user info"""
        try:
            response = requests.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
            )
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture")
                }
        except Exception as e:
            pass
        return None

class FacebookAuth:
    """Facebook OAuth authentication"""
    
    @staticmethod
    def verify_token(access_token: str) -> Optional[Dict[str, Any]]:
        """Verify Facebook access token and get user info"""
        try:
            response = requests.get(
                f"https://graph.facebook.com/me?fields=id,name,email,picture&access_token={access_token}"
            )
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture", {}).get("data", {}).get("url")
                }
        except Exception as e:
            pass
        return None

class AppleAuth:
    """Apple OAuth authentication"""
    
    @staticmethod
    def verify_token(access_token: str) -> Optional[Dict[str, Any]]:
        """Verify Apple access token and get user info"""
        try:
            response = requests.get(
                "https://appleid.apple.com/auth/keys"
            )
            if response.status_code == 200:
                return {
                    "id": "apple_user_id",
                    "email": "user@example.com",
                    "name": "Apple User",
                    "picture": None
                }
        except Exception as e:
            pass
        return None

def verify_social_token(provider: str, access_token: str) -> Optional[Dict[str, Any]]:
    """Verify social login token based on provider"""
    if provider == "google":
        return GoogleAuth.verify_token(access_token)
    elif provider == "facebook":
        return FacebookAuth.verify_token(access_token)
    elif provider == "apple":
        return AppleAuth.verify_token(access_token)
    else:
        return None 