from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.app.core import security


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(data: dict) -> str:
    """Synchronous access-token creation (delegates to core.security)."""
    return security.create_access_token(data)


async def create_access_token_async(data: dict) -> str:
    """Async variant kept for call-sites that need ``await``."""
    return security.create_access_token(data)


def verify_access_token(token: str) -> str:
    """Synchronous token verification (delegates to core.security)."""
    return security.decode_access_token(token)


async def verify_access_token_async(token: str) -> str:
    """Async variant kept for call-sites that need ``await``."""
    return security.decode_access_token(token)
