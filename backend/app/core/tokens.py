from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.app.core import security


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_access_token(data: dict) -> str:
    # delegates to core.security.create_access_token (sync)
    return security.create_access_token(data)


async def verify_access_token(token: str) -> str:
    # delegates to core.security.decode_access_token which raises HTTPException on invalid
    return security.decode_access_token(token)
