import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


try:
    # Newer versions
    from agora_token_builder import RtcTokenBuilder2, Role
    _RTC = RtcTokenBuilder2
    _ROLE_PUBLISHER = Role.PUBLISHER
    _ROLE_SUBSCRIBER = Role.SUBSCRIBER
except Exception:
    # Fallback for older versions
    from agora_token_builder import RtcTokenBuilder as RtcTokenBuilder2  # type: ignore
    _RTC = RtcTokenBuilder2  # type: ignore

    class _Role:  # type: ignore
        PUBLISHER = 1
        SUBSCRIBER = 2

    _ROLE_PUBLISHER = _Role.PUBLISHER
    _ROLE_SUBSCRIBER = _Role.SUBSCRIBER


_AGORA_APP_ID: Optional[str] = os.getenv("AGORA_APP_ID") or None
_AGORA_APP_CERT: Optional[str] = os.getenv("AGORA_APP_CERTIFICATE") or None


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
    expire_at = int((datetime.utcnow() + timedelta(seconds=expire_seconds)).timestamp())

    if user_account is not None and user_account != "":
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


