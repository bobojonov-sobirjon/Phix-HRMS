import requests
import jwt
from typing import Optional, Dict, Any
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from ..core.config import settings

# Firebase public keys cache
_firebase_public_keys = None


def get_firebase_public_keys() -> Dict[str, Any]:
    """
    Get Firebase public keys for JWT verification (without SDK)
    
    Returns parsed public keys ready for PyJWT
    """
    global _firebase_public_keys
    
    try:
        # Fetch Google's public keys (X.509 certificates)
        response = requests.get(
            "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com",
            timeout=5
        )
        
        if response.status_code == 200:
            certs = response.json()
            
            # Parse X.509 certificates to get public keys
            parsed_keys = {}
            for kid, cert_string in certs.items():
                try:
                    # Convert certificate string to bytes
                    cert_bytes = cert_string.encode('utf-8')
                    
                    # Load X.509 certificate
                    cert = load_pem_x509_certificate(cert_bytes, default_backend())
                    
                    # Extract public key from certificate
                    public_key = cert.public_key()
                    
                    # Store parsed public key
                    parsed_keys[kid] = public_key
                    
                except Exception:
                    continue
            
            _firebase_public_keys = parsed_keys
            return _firebase_public_keys
        
        return {}
        
    except Exception:
        return {}


class FirebaseAuth:
    """Firebase Authentication - Verify ID tokens WITHOUT Firebase Admin SDK"""
    
    @staticmethod
    def verify_token(id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token manually (without Firebase Admin SDK)
        
        This verifies tokens from:
        - Google Sign-In via Firebase
        - Facebook Login via Firebase  
        - Apple Sign-In via Firebase
        - Email/Password via Firebase
        
        Args:
            id_token: Firebase ID token (JWT format)
            
        Returns:
            User information dict or None if verification fails
        """
        try:
            # Decode token header to get key ID (kid)
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get('kid')
            
            if not kid:
                return None
            
            # Get Firebase public keys
            public_keys = get_firebase_public_keys()
            
            if kid not in public_keys:
                return None
            
            # Get the public key for this token
            public_key = public_keys[kid]
            
            # Verify and decode the token
            decoded_token = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=settings.FIREBASE_PROJECT_ID,
                issuer=f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}"
            )
            
            # Extract user information
            user_info = {
                "id": decoded_token.get("user_id") or decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "email_verified": decoded_token.get("email_verified", False),
                "provider": decoded_token.get("firebase", {}).get("sign_in_provider", "unknown")
            }
            
            return user_info
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception):
            return None


def verify_social_token(provider: str, id_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify social login token from Firebase Authentication
    
    Args:
        provider: Social provider (google, facebook, apple) - kept for API compatibility
        id_token: Firebase ID token (JWT format)
        
    Returns:
        User information dict or None if verification fails
        
    Note:
        All providers (Google, Facebook, Apple) use Firebase Authentication,
        so we verify the Firebase ID token regardless of provider.
        This function does NOT require Firebase Admin SDK.
    """
    try:
        # Verify Firebase JWT token manually
        user_info = FirebaseAuth.verify_token(id_token)
        
        if user_info:
            # Add requested provider info
            if provider:
                user_info["requested_provider"] = provider
            
            return user_info
        
        return None
        
    except Exception:
        return None 