import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


try:
    # Use RtcTokenBuilder for 007 format
    from agora_token_builder import RtcTokenBuilder
    _RTC = RtcTokenBuilder
    
    # Define roles manually since Role class doesn't exist
    class _Role:
        PUBLISHER = 1
        SUBSCRIBER = 2
    
    _ROLE_PUBLISHER = _Role.PUBLISHER
    _ROLE_SUBSCRIBER = _Role.SUBSCRIBER
except Exception as e:
    print(f"Error importing agora_token_builder: {e}")
    raise


_AGORA_APP_ID: Optional[str] = os.getenv("AGORA_APP_ID") or "e406a7515b244f6b968ab0520532609a"
_AGORA_APP_CERT: Optional[str] = os.getenv("AGORA_APP_CERTIFICATE") or "87beeaa4750340c281e9d7abb79fa1de"


def set_agora_credentials(app_id: str, app_certificate: str) -> None:
    """
    Set Agora credential values in-memory for token generation.

    Args:
        app_id: Agora project App ID
        app_certificate: Agora project App Certificate (primary key)
    """
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
    if not _AGORA_APP_ID:
        raise ValueError(
            "Agora App ID is not set. Call set_agora_credentials(app_id, app_certificate) "
            "or set AGORA_APP_ID environment variable."
        )
    if not _AGORA_APP_CERT:
        raise ValueError(
            "Agora App Certificate is not set. Call set_agora_credentials(app_id, app_certificate) "
            "or set AGORA_APP_CERTIFICATE environment variable."
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
    # Use current time + expire_seconds for token expiration
    expire_at = int((datetime.now().timestamp() + expire_seconds))

    # Debug logging
    print(f"DEBUG: Generating token with:")
    print(f"  App ID: {_AGORA_APP_ID}")
    print(f"  App Cert: {_AGORA_APP_CERT}")
    print(f"  Channel: {channel_name}")
    print(f"  UID: {uid}")
    print(f"  User Account: {user_account}")
    print(f"  Role: {role} -> {target_role}")
    print(f"  Expire: {expire_at}")

    if user_account is not None and user_account != "":
        # Use buildTokenWithAccount for 007 format
        token = _RTC.buildTokenWithAccount(
            _AGORA_APP_ID,  # type: ignore[arg-type]
            _AGORA_APP_CERT,  # type: ignore[arg-type]
            channel_name,
            user_account,
            target_role,
            expire_at,
        )
        uid_return: Optional[int] = None
        account_return: Optional[str] = user_account
    else:
        numeric_uid = int(uid or 0)
        # Use buildTokenWithUid for 007 format
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

    print(f"DEBUG: Generated token: {token[:50]}...")

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


