from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import settings
from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# ── Password helpers ────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


_COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "admin",
}


def validate_password_strength(password: str) -> bool:
    if not password or len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    if password.lower() in _COMMON_PASSWORDS:
        return False
    return has_upper and has_lower and has_digit and has_special


# ── Access tokens ───────────────────────────────────────────────────────


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    if "jti" not in to_encode:
        to_encode["jti"] = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        # Try current key first, then previous keys for rotation support
        last_error = None
        for key in settings.all_secret_keys:
            try:
                payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
                user_id: str | None = payload.get("sub")
                if user_id is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
                return user_id
            except JWTError as e:
                last_error = e
                continue
        raise last_error or JWTError("No valid key found")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")


def verify_access_token(token: str) -> str:
    return decode_access_token(token)


async def revoke_access_token(jti: str, expires_in_minutes: int = 30) -> None:
    """Revoke an access token by storing its jti in Redis."""
    try:
        await redis_cache.set(
            f"revoked_access:{jti}",
            True,
            expire_seconds=expires_in_minutes * 60,
        )
    except Exception:
        logger.error("Failed to revoke access token %s in Redis — token may remain valid", jti, exc_info=True)


async def is_access_token_revoked(jti: str) -> bool:
    """Check if an access token has been revoked."""
    try:
        val = await redis_cache.get(f"revoked_access:{jti}")
        return bool(val)
    except Exception:
        logger.error("Redis unavailable checking revoked token %s — rejecting request", jti, exc_info=True)
        return True


async def create_access_token_async(data: dict) -> str:
    return create_access_token(data)


# ── Refresh tokens (two-tier storage: Redis + in-memory fallback) ────────

REFRESH_EXPIRE_DAYS = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)
_TTL_SECONDS = REFRESH_EXPIRE_DAYS * 24 * 3600

# NOTE: In-memory token stores are NOT process-safe. In a multi-worker setup
# (e.g. gunicorn with multiple workers), each worker has its own memory space.
# Revocation and active-token state in _memory_active/_memory_revoked will NOT
# be shared across workers. Redis is the authoritative store; in-memory dicts
# are fast-lookup caches only. If Redis is unavailable, in-memory fallback may
# allow revoked tokens to be accepted by a different worker process.
_memory_active: dict[str, float] = {}
_memory_revoked: dict[str, float] = {}
_memory_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _mem_cleanup_expired() -> None:
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
        return bool(exp is not None and exp > _now().timestamp())


def _mem_is_active(jti: str) -> bool:
    with _memory_lock:
        exp = _memory_active.get(jti)
        return bool(exp is not None and exp > _now().timestamp())


async def _store_token(jti: str, user_id: int) -> None:
    # Store in Redis FIRST (primary), then cache in memory
    try:
        await redis_cache.set(
            f"refresh:{jti}",
            {"user_id": user_id},
            expire_seconds=_TTL_SECONDS,
        )
    except Exception:
        logger.error("Failed to store refresh token %s in Redis", jti, exc_info=True)
    # Always cache in memory for fast lookups
    _mem_store_active(jti)


async def _revoke_token(jti: str) -> None:
    # Revoke in Redis FIRST (primary), then mark in memory
    try:
        await redis_cache.delete(f"refresh:{jti}")
        await redis_cache.set(
            f"revoked_refresh:{jti}",
            True,
            expire_seconds=_TTL_SECONDS,
        )
    except Exception:
        logger.error("Failed to revoke refresh token %s in Redis", jti, exc_info=True)
    _mem_store_revoked(jti)


async def _is_revoked(jti: str) -> bool:
    # Check Redis first (source of truth), then memory cache
    try:
        val = await redis_cache.get(f"revoked_refresh:{jti}")
        if val:
            return True
    except Exception:
        logger.debug("Redis unavailable checking revoked token %s", jti, exc_info=True)
    return bool(_mem_is_revoked(jti))


async def _is_active(jti: str) -> bool:
    # Check Redis first (source of truth), then memory cache
    try:
        stored = await redis_cache.get(f"refresh:{jti}")
        if stored:
            return True
    except Exception:
        logger.debug("Redis unavailable checking active token %s", jti, exc_info=True)
    return bool(_mem_is_active(jti))


async def create_refresh_token(user_id: int) -> dict:
    jti = str(uuid.uuid4())
    expire = _now() + timedelta(days=REFRESH_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    await _store_token(jti, user_id)
    return {"token": token, "jti": jti, "expires_at": expire.isoformat()}


async def verify_refresh_token(token: str) -> dict | None:
    if not token:
        return None
    try:
        # Try current key first, then previous keys for rotation support
        payload = None
        for key in settings.all_secret_keys:
            try:
                payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
                break
            except JWTError:
                continue
        if payload is None:
            return None
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            return None
        if await _is_revoked(jti):
            return None
        if await _is_active(jti):
            return {"jti": jti, "user_id": int(user_id)}
        return {"jti": jti, "user_id": int(user_id)}
    except JWTError:
        return None


async def revoke_refresh_token_by_jti(jti: str) -> bool:
    await _revoke_token(jti)
    return True


async def rotate_refresh_token(old_jti: str, user_id: int) -> dict | None:
    already_revoked = await _is_revoked(old_jti)
    if already_revoked:
        return None
    await _revoke_token(old_jti)
    return await create_refresh_token(user_id)


async def is_refresh_revoked(jti: str) -> bool:
    return await _is_revoked(jti)
