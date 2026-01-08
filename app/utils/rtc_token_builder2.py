"""
RtcTokenBuilder2 for generating 007 format Agora tokens
Based on Agora's official RtcTokenBuilder2 implementation
"""
import hmac
import hashlib
import base64
import struct
import time
from typing import Optional


class Role:
    PUBLISHER = 1
    SUBSCRIBER = 2


class RtcTokenBuilder2:
    """Generate 007 format Agora RTC tokens"""
    
    @staticmethod
    def build_token_with_uid(
        app_id: str,
        app_certificate: str,
        channel_name: str,
        uid: int,
        role: int,
        token_expiration_in_seconds: int,
        privilege_expiration_in_seconds: int
    ) -> str:
        """
        Build token with uid for 007 format
        
        Args:
            app_id: Agora App ID
            app_certificate: Agora App Certificate
            channel_name: Channel name
            uid: User ID (integer)
            role: Role (1 for publisher, 2 for subscriber)
            token_expiration_in_seconds: Token expiration time
            privilege_expiration_in_seconds: Privilege expiration time
            
        Returns:
            007 format token string
        """
        return RtcTokenBuilder2._build_token(
            app_id=app_id,
            app_certificate=app_certificate,
            channel_name=channel_name,
            uid=uid,
            user_account=None,
            role=role,
            token_expiration_in_seconds=token_expiration_in_seconds,
            privilege_expiration_in_seconds=privilege_expiration_in_seconds
        )
    
    @staticmethod
    def build_token_with_user_account(
        app_id: str,
        app_certificate: str,
        channel_name: str,
        user_account: str,
        role: int,
        token_expiration_in_seconds: int,
        privilege_expiration_in_seconds: int
    ) -> str:
        """
        Build token with user account for 007 format
        
        Args:
            app_id: Agora App ID
            app_certificate: Agora App Certificate
            channel_name: Channel name
            user_account: User account (string)
            role: Role (1 for publisher, 2 for subscriber)
            token_expiration_in_seconds: Token expiration time
            privilege_expiration_in_seconds: Privilege expiration time
            
        Returns:
            007 format token string
        """
        return RtcTokenBuilder2._build_token(
            app_id=app_id,
            app_certificate=app_certificate,
            channel_name=channel_name,
            uid=None,
            user_account=user_account,
            role=role,
            token_expiration_in_seconds=token_expiration_in_seconds,
            privilege_expiration_in_seconds=privilege_expiration_in_seconds
        )
    
    @staticmethod
    def _build_token(
        app_id: str,
        app_certificate: str,
        channel_name: str,
        uid: Optional[int],
        user_account: Optional[str],
        role: int,
        token_expiration_in_seconds: int,
        privilege_expiration_in_seconds: int
    ) -> str:
        """Internal method to build 007 format token"""
        current_timestamp = int(time.time())
        token_expire = current_timestamp + token_expiration_in_seconds
        privilege_expire = current_timestamp + privilege_expiration_in_seconds
        
        
        version = struct.pack('>H', 7)
        
        app_id_bytes = app_id.encode('utf-8')
        app_id_length = struct.pack('>H', len(app_id_bytes))
        
        channel_name_bytes = channel_name.encode('utf-8')
        channel_name_length = struct.pack('>H', len(channel_name_bytes))
        
        if user_account:
            uid_bytes = user_account.encode('utf-8')
        else:
            uid_bytes = struct.pack('>I', uid if uid else 0)
        uid_length = struct.pack('>H', len(uid_bytes))
        
        token_expire_bytes = struct.pack('>I', token_expire)
        privilege_expire_bytes = struct.pack('>I', privilege_expire)
        
        role_byte = struct.pack('B', role)
        
        if role == Role.PUBLISHER:
            privileges = struct.pack('>I', 0xFFFFFFFF)
        else:
            privileges = struct.pack('>I', 0x1)
        
        content = (
            version +
            app_id_length + app_id_bytes +
            channel_name_length + channel_name_bytes +
            uid_length + uid_bytes +
            token_expire_bytes +
            privilege_expire_bytes +
            role_byte +
            privileges
        )
        
        signature = hmac.new(
            app_certificate.encode('utf-8'),
            content,
            hashlib.sha256
        ).digest()
        
        token = signature + content
        
        token_b64 = base64.b64encode(token).decode('utf-8')
        
        return "007" + token_b64
