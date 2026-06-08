from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError

from backend.app.core.config import settings
from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)

SECRET = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
REFRESH_EXPIRE_DAYS = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Async versions ────────────────────────────────────────────────────

async def create_refresh_token(user_id: int) -> dict:
    jti = str(uuid.uuid4())
    expire = _now() + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire}
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    await redis_cache.set(f"refresh:{jti}", {"user_id": user_id}, expire_seconds=REFRESH_EXPIRE_DAYS * 24 * 3600)
    return {"token": token, "jti": jti, "expires_at": expire.isoformat()}


async def verify_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            return None
        stored = await redis_cache.get(f"refresh:{jti}")
        if not stored:
            return None
        return {"jti": jti, "user_id": int(user_id)}
    except JWTError:
        return None


async def revoke_refresh_token_by_jti(jti: str) -> bool:
    await redis_cache.delete(f"refresh:{jti}")
    await redis_cache.set(f"revoked_refresh:{jti}", True, expire_seconds=REFRESH_EXPIRE_DAYS * 24 * 3600)
    return True


async def rotate_refresh_token(old_jti: str, user_id: int) -> dict:
    await revoke_refresh_token_by_jti(old_jti)
    return await create_refresh_token(user_id)


async def is_refresh_revoked(jti: str) -> bool:
    val = await redis_cache.get(f"revoked_refresh:{jti}")
    return bool(val)


# ── Sync version (for sync auth endpoints in threadpool) ─────────────
# Only create_refresh_token_sync is used — register/login need a
# refresh token but the rest of the flow (verify/revoke/rotate) is
# handled by the async variants above.

def create_refresh_token_sync(user_id: int) -> dict:
    """Create a refresh token. Returns token dict or a fallback on Redis failure."""
    jti = str(uuid.uuid4())
    expire = _now() + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire}
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    try:
        redis_cache.run_sync(
            redis_cache.set(f"refresh:{jti}", {"user_id": user_id}, expire_seconds=REFRESH_EXPIRE_DAYS * 24 * 3600)
        )
    except Exception as e:
        logger.warning("Failed to store refresh token in Redis: %s", e)
    return {"token": token, "jti": jti, "expires_at": expire.isoformat()}
