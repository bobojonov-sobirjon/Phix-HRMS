from datetime import datetime, timedelta
from typing import Optional, Dict, Any


try:
    # Try to import RtcTokenBuilder2 for 007 format
    try:
        from agora_token_builder.RtcTokenBuilder2 import RtcTokenBuilder2
        _RTC = RtcTokenBuilder2
        _USE_NEW_API = True
        _HAS_ACCESS_TOKEN2 = False
        print("Using RtcTokenBuilder2 (007 format) from agora_token_builder.RtcTokenBuilder2")
    except ImportError:
        # Try official RtcTokenBuilder2 from Agora GitHub
        try:
            from .rtc_token_builder2_official import RtcTokenBuilder2
            _RTC = RtcTokenBuilder2
            _USE_NEW_API = True
            _HAS_ACCESS_TOKEN2 = False
            print("Using official RtcTokenBuilder2 (007 format) from Agora GitHub")
        except ImportError:
            # Try our local implementation of RtcTokenBuilder2
            try:
                from .rtc_token_builder2 import RtcTokenBuilder2
                _RTC = RtcTokenBuilder2
                _USE_NEW_API = True
                _HAS_ACCESS_TOKEN2 = False
                print("Using local RtcTokenBuilder2 (007 format) implementation")
            except ImportError:
                # Try to import AccessToken2 for 007 format
                try:
                    from agora_access_token2 import AccessToken2, ServiceRtc, ServiceRtm
                    _HAS_ACCESS_TOKEN2 = True
                    _USE_NEW_API = False
                    print("Using AccessToken2 (007 format)")
                except ImportError:
                    _HAS_ACCESS_TOKEN2 = False
                    # Fallback to standard RtcTokenBuilder (006 format)
                    from agora_token_builder import RtcTokenBuilder
                    _RTC = RtcTokenBuilder
                    _USE_NEW_API = False
                    print("Using standard RtcTokenBuilder (006 format)")
    
    # Define roles for 007 format
    try:
        from agora_token_builder import Role_Publisher, Role_Subscriber
        _ROLE_PUBLISHER = Role_Publisher
        _ROLE_SUBSCRIBER = Role_Subscriber
    except ImportError:
        # Fallback: define roles manually
        class _Role:
            PUBLISHER = 1
            SUBSCRIBER = 2
        _ROLE_PUBLISHER = _Role.PUBLISHER
        _ROLE_SUBSCRIBER = _Role.SUBSCRIBER
except Exception as e:
    print(f"Error importing agora_token_builder: {e}")
    raise


# Default credentials (hard-coded as requested)
_AGORA_APP_ID: Optional[str] = "e406a7515b244f6b968ab0520532609a"
_AGORA_APP_CERT: Optional[str] = "87beeaa4750340c281e9d7abb79fa1de"




def set_agora_credentials(app_id: str, app_certificate: str) -> None:
    """Set Agora credential values in-memory for token generation."""
    global _AGORA_APP_ID, _AGORA_APP_CERT
    _AGORA_APP_ID = app_id
    _AGORA_APP_CERT = app_certificate


def get_agora_credentials() -> Dict[str, Optional[str]]:
    """Return current Agora credentials (may be None if unset)."""
    return {
        "appId": _AGORA_APP_ID,
        "appCertificate": _AGORA_APP_CERT,
    }


def _require_credentials() -> None:
    if not _AGORA_APP_ID or not _AGORA_APP_CERT:
        raise ValueError(
            "Agora credentials are not set. Call set_agora_credentials(app_id, app_certificate) "
            "or set AGORA_APP_ID and AGORA_APP_CERTIFICATE environment variables."
        )


def _resolve_role(role: str) -> int:
    normalized = role.strip().lower()
    if normalized in ("publisher", "host", "pub"):
        return _ROLE_PUBLISHER
    return _ROLE_SUBSCRIBER


def generate_rtc_token(
    channel_name: str,
    uid: Optional[int] = None,
    user_account: Optional[str] = None,
    role: str = "publisher",
    expire_seconds: int = 3600,
) -> Dict[str, Any]:
    """
    Generate an Agora RTC token for a given channel.

    Args:
        channel_name: Channel name to join
        uid: Numeric UID (0 lets Agora assign). Use either uid or user_account
        user_account: String-based UID (use either uid or user_account)
        role: 'publisher' (host) or 'subscriber' (audience)
        expire_seconds: Token validity in seconds (min 60, max 86400)

    Returns:
        Dict containing token data including token string and metadata
    """
    _require_credentials()

    if not channel_name or not channel_name.strip():
        raise ValueError("channel_name is required")

    if expire_seconds < 60 or expire_seconds > 24 * 60 * 60:
        raise ValueError("expire_seconds must be between 60 and 86400")

    target_role = _resolve_role(role)
    expire_at = int((datetime.now().timestamp() + expire_seconds))
    privilege_expiration = expire_at  # Privilege expiration same as token expiration (007 format)

    # Use AccessToken2 for 007 format if available
    if _HAS_ACCESS_TOKEN2:
        # Generate 007 format token using AccessToken2
        from agora_access_token2 import AccessToken2, ServiceRtc
        
        app_cert = _AGORA_APP_CERT
        app_id = _AGORA_APP_ID
        
        # Create AccessToken2 instance
        token_builder = AccessToken2(app_id, app_cert, expire_at)
        
        # Add RTC service
        service_rtc = ServiceRtc(app_id, channel_name)
        
        if user_account is not None and user_account != "":
            # Use user account (string UID)
            service_rtc.add_privilege(ServiceRtc.PrivilegeJoinChannel, privilege_expiration)
            service_rtc.add_privilege(ServiceRtc.PrivilegePublishAudioStream, privilege_expiration)
            service_rtc.add_privilege(ServiceRtc.PrivilegePublishVideoStream, privilege_expiration)
            service_rtc.add_privilege(ServiceRtc.PrivilegePublishDataStream, privilege_expiration)
            token_builder.add_service(service_rtc)
            token = token_builder.build(user_account)
            uid_return: Optional[int] = None
            account_return: Optional[str] = user_account
        else:
            # Use numeric UID
            numeric_uid = int(uid or 0)
            service_rtc.add_privilege(ServiceRtc.PrivilegeJoinChannel, privilege_expiration)
            service_rtc.add_privilege(ServiceRtc.PrivilegePublishAudioStream, privilege_expiration)
            service_rtc.add_privilege(ServiceRtc.PrivilegePublishVideoStream, privilege_expiration)
            service_rtc.add_privilege(ServiceRtc.PrivilegePublishDataStream, privilege_expiration)
            token_builder.add_service(service_rtc)
            token = token_builder.build(uid=numeric_uid)
            uid_return = numeric_uid
            account_return = None
    elif _USE_NEW_API:
        # Use 007 format API (build_token_with_uid/build_token_with_user_account)
        # These methods generate tokens that start with "007" instead of "006"
        # Note: RtcTokenBuilder2 uses token_expire and privilege_expire in seconds (not timestamps)
        if user_account is not None and user_account != "":
            # Use build_token_with_user_account for 007 format
            token = _RTC.build_token_with_user_account(
                _AGORA_APP_ID,  # type: ignore[arg-type]
                _AGORA_APP_CERT,  # type: ignore[arg-type]
                channel_name,
                user_account,
                target_role,
                expire_seconds,  # token_expire (in seconds)
                expire_seconds,  # privilege_expire (in seconds)
            )
            uid_return: Optional[int] = None
            account_return: Optional[str] = user_account
        else:
            numeric_uid = int(uid or 0)
            # Use build_token_with_uid for 007 format
            token = _RTC.build_token_with_uid(
                _AGORA_APP_ID,  # type: ignore[arg-type]
                _AGORA_APP_CERT,  # type: ignore[arg-type]
                channel_name,
                numeric_uid,
                target_role,
                expire_seconds,  # token_expire (in seconds)
                expire_seconds,  # privilege_expire (in seconds)
            )
            uid_return = numeric_uid
            account_return = None
    else:
        numeric_uid = int(uid or 0)
        # Try new 007 format API first (snake_case methods)
        if hasattr(_RTC, 'build_token_with_uid'):
            try:
                token = _RTC.build_token_with_uid(
                    _AGORA_APP_ID,  # type: ignore[arg-type]
                    _AGORA_APP_CERT,  # type: ignore[arg-type]
                    channel_name,
                    numeric_uid,
                    target_role,
                    expire_at,
                    privilege_expiration,
                )
                uid_return = numeric_uid
                account_return = None
            except TypeError:
                # If privilege_expiration parameter not supported, try without it
                token = _RTC.build_token_with_uid(
                    _AGORA_APP_ID,  # type: ignore[arg-type]
                    _AGORA_APP_CERT,  # type: ignore[arg-type]
                    channel_name,
                    numeric_uid,
                    target_role,
                    expire_at,
                )
                uid_return = numeric_uid
                account_return = None
        elif hasattr(_RTC, 'buildTokenWithUid'):
            # Fallback to camelCase API (006 format)
            token = _RTC.buildTokenWithUid(
                _AGORA_APP_ID,  # type: ignore[arg-type]
                _AGORA_APP_CERT,  # type: ignore[arg-type]
                channel_name,
                numeric_uid,
                target_role,
                expire_at,
            )
            uid_return = numeric_uid
            account_return = None
        else:
            raise ValueError("No suitable token builder method found for uid")
    
    # Verify token format (007 format tokens start with "007")
    if token and token.startswith("007"):
        print(f"Generated 007 format token (length: {len(token)})")
    elif token and token.startswith("006"):
        print(f"Warning: Generated 006 format token instead of 007. Token length: {len(token)}")
    else:
        print(f"Generated token (format unknown, length: {len(token)})")

    return {
        "appId": _AGORA_APP_ID,
        "channel": channel_name,
        "uid": uid_return,
        "userAccount": account_return,
        "role": "publisher" if target_role == _ROLE_PUBLISHER else "subscriber",
        "expireAt": expire_at,
        "token": token,
    }


__all__ = [
    "set_agora_credentials",
    "get_agora_credentials",
    "generate_rtc_token",
]


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate Agora RTC token (standalone)")
    parser.add_argument("channel", nargs="?", default="demo", help="Channel name to join (default: demo)")
    parser.add_argument("--uid", type=int, default=None, help="Numeric UID (0 lets Agora assign). Use either --uid or --account")
    parser.add_argument("--account", type=str, default=None, help="String user account (use either --uid or --account)")
    parser.add_argument("--role", type=str, default="publisher", choices=["publisher", "subscriber", "host", "pub"], help="Role for token")
    parser.add_argument("--expire", type=int, default=3600, help="Token expiry in seconds (60..86400)")
    parser.add_argument("--app-id", type=str, default=None, help="Override Agora App ID (else env/defaults)")
    parser.add_argument("--app-cert", type=str, default=None, help="Override Agora App Certificate (else env/defaults)")

    args = parser.parse_args()

    if args.app_id and args.app_cert:
        set_agora_credentials(args.app_id, args.app_cert)

    try:
        result = generate_rtc_token(
            channel_name=args.channel,
            uid=args.uid,
            user_account=args.account,
            role=args.role,
            expire_seconds=args.expire,
        )
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)

    # Do not print certificate; return only necessary fields
    safe = {
        "appId": result.get("appId"),
        "channel": result.get("channel"),
        "uid": result.get("uid"),
        "userAccount": result.get("userAccount"),
        "role": result.get("role"),
        "expireAt": result.get("expireAt"),
        "token": result.get("token"),
    }
    print(json.dumps(safe, ensure_ascii=False))
