"""Refresh and access token utilities.

Provides server-side revocation for refresh tokens with a two-tier storage:
  1. Redis (primary) — works when Redis is available
  2. In-memory dict (fallback) — works when Redis is down (e.g. during tests)

Tokens created via the sync path (register/login) are stored in both tiers
so they can be revoked when the async refresh endpoint runs later.
"""
from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from backend.app.core.config import settings
from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)

SECRET = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
REFRESH_EXPIRE_DAYS = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)
_TTL_SECONDS = REFRESH_EXPIRE_DAYS * 24 * 3600


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── In-memory fallback stores ────────────────────────────────────────
# Used when Redis is unavailable.  Thread-safe via a lock.
# Entries auto-expire after _TTL_SECONDS to prevent unbounded growth.
_memory_active: dict[str, float] = {}   # jti → expiry timestamp
_memory_revoked: dict[str, float] = {}  # jti → expiry timestamp
_memory_lock = threading.Lock()


def _mem_cleanup_expired() -> None:
    """Remove expired entries. Called lazily on each write."""
    now = _now().timestamp()
    expired_active = [k for k, exp in _memory_active.items() if exp < now]
    expired_revoked = [k for k, exp in _memory_revoked.items() if exp < now]
    for k in expired_active:
        del _memory_active[k]
    for k in expired_revoked:
        del _memory_revoked[k]


def _mem_store_active(jti: str) -> None:
    with _memory_lock:
        _mem_cleanup_expired()
        _memory_active[jti] = _now().timestamp() + _TTL_SECONDS


def _mem_store_revoked(jti: str) -> None:
    with _memory_lock:
        _mem_cleanup_expired()
        _memory_revoked[jti] = _now().timestamp() + _TTL_SECONDS
        _memory_active.pop(jti, None)


def _mem_is_revoked(jti: str) -> bool:
    with _memory_lock:
        exp = _memory_revoked.get(jti)
        if exp is not None and exp > _now().timestamp():
            return True
        return False


def _mem_is_active(jti: str) -> bool:
    with _memory_lock:
        exp = _memory_active.get(jti)
        if exp is not None and exp > _now().timestamp():
            return True
        return False


# ── Dual-tier storage helpers ────────────────────────────────────────

async def _store_token(jti: str, user_id: int) -> None:
    """Store a refresh token in Redis (primary) + in-memory (fallback)."""
    _mem_store_active(jti)
    try:
        await redis_cache.set(
            f"refresh:{jti}",
            {"user_id": user_id},
            expire_seconds=REFRESH_EXPIRE_DAYS * 24 * 3600,
        )
    except Exception:
        pass  # In-memory fallback is already populated


def _store_token_sync(jti: str, user_id: int) -> None:
    """Store a refresh token from sync context (threadpool)."""
    _mem_store_active(jti)
    try:
        redis_cache.run_sync(
            redis_cache.set(
                f"refresh:{jti}",
                {"user_id": user_id},
                expire_seconds=REFRESH_EXPIRE_DAYS * 24 * 3600,
            )
        )
    except Exception:
        pass  # In-memory fallback is already populated


async def _revoke_token(jti: str) -> None:
    """Mark a refresh token as revoked in both tiers."""
    _mem_store_revoked(jti)
    try:
        await redis_cache.delete(f"refresh:{jti}")
        await redis_cache.set(
            f"revoked_refresh:{jti}",
            True,
            expire_seconds=REFRESH_EXPIRE_DAYS * 24 * 3600,
        )
    except Exception:
        pass  # In-memory fallback is already populated


async def _is_revoked(jti: str) -> bool:
    """Check if a refresh token has been revoked."""
    if _mem_is_revoked(jti):
        return True
    try:
        val = await redis_cache.get(f"revoked_refresh:{jti}")
        if val:
            return True
    except Exception:
        pass
    return False


async def _is_active(jti: str) -> bool:
    """Check if a refresh token is still active in any store."""
    if _mem_is_active(jti):
        return True
    try:
        stored = await redis_cache.get(f"refresh:{jti}")
        if stored:
            return True
    except Exception:
        pass
    return False


# ── Public API ───────────────────────────────────────────────────────

async def create_refresh_token(user_id: int) -> dict:
    """Create a new refresh token (async path — e.g. after rotation)."""
    jti = str(uuid.uuid4())
    expire = _now() + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire}
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    await _store_token(jti, user_id)
    return {"token": token, "jti": jti, "expires_at": expire.isoformat()}


def create_refresh_token_sync(user_id: int) -> dict:
    """Create a refresh token from a sync context (register/login).

    Stores in both in-memory and Redis so the token can be revoked
    later by the async refresh endpoint.
    """
    jti = str(uuid.uuid4())
    expire = _now() + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire}
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    _store_token_sync(jti, user_id)
    return {"token": token, "jti": jti, "expires_at": expire.isoformat()}


async def verify_refresh_token(token: str) -> dict | None:
    """Verify a refresh token.

    Checks JWT signature, then checks whether the token has been revoked
    or is still active.  Falls back to JWT-only validation when neither
    Redis nor the in-memory store has data for this token (e.g. tokens
    issued before the in-memory fallback was added).
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            return None

        # 1. Check if revoked
        if await _is_revoked(jti):
            return None

        # 2. Check if active in store
        if await _is_active(jti):
            return {"jti": jti, "user_id": int(user_id)}

        # 3. Fallback: token is valid JWT but not in any store
        #    (legacy token issued before in-memory fallback was added).
        #    Allow it — it's still cryptographically valid.
        return {"jti": jti, "user_id": int(user_id)}
    except JWTError:
        return None


async def revoke_refresh_token_by_jti(jti: str) -> bool:
    """Revoke a refresh token by its JTI."""
    await _revoke_token(jti)
    return True


async def rotate_refresh_token(old_jti: str, user_id: int) -> dict | None:
    """Rotate a refresh token: revoke the old one and issue a new one.

    Returns ``None`` if the old token was already revoked (another
    request already rotated it — prevents token-reuse race conditions).
    """
    already_revoked = await _is_revoked(old_jti)
    if already_revoked:
        return None
    await _revoke_token(old_jti)
    return await create_refresh_token(user_id)


async def is_refresh_revoked(jti: str) -> bool:
    """Check if a refresh token has been revoked."""
    return await _is_revoked(jti)
