from __future__ import annotations

from typing import Tuple
import logging
import time

from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)

FAIL_PREFIX = "auth_fail:"  # keyed by ip:username
BLOCK_PREFIX = "auth_block:"  # keyed by ip or username

# Timeout for Redis operations during auth — fail open if exceeded
REDIS_AUTH_TIMEOUT = 3.0


# ── Async versions (used by background tasks) ─────────────────────────

async def record_login_failure(ip: str, username: str, max_attempts: int = 5, window_seconds: int = 300) -> Tuple[int, bool]:
    key = f"{FAIL_PREFIX}{ip}:{username}"
    val = await redis_cache.get(key) or {"count": 0, "first": time.time()}
    val["count"] = val.get("count", 0) + 1
    await redis_cache.set(key, val, expire_seconds=window_seconds)
    blocked = val["count"] >= max_attempts
    if blocked:
        await redis_cache.set(f"{BLOCK_PREFIX}ip:{ip}", True, expire_seconds=window_seconds)
        await redis_cache.set(f"{BLOCK_PREFIX}user:{username}", True, expire_seconds=window_seconds)
    return val["count"], blocked


async def reset_login_failures(ip: str, username: str):
    key = f"{FAIL_PREFIX}{ip}:{username}"
    await redis_cache.delete(key)
    await redis_cache.delete(f"{BLOCK_PREFIX}ip:{ip}")
    await redis_cache.delete(f"{BLOCK_PREFIX}user:{username}")


async def is_blocked(ip: str, username: str) -> bool:
    ip_block = await redis_cache.get(f"{BLOCK_PREFIX}ip:{ip}")
    user_block = await redis_cache.get(f"{BLOCK_PREFIX}user:{username}")
    return bool(ip_block) or bool(user_block)


# ── Sync versions (used by sync auth endpoints in threadpool) ─────────

def is_blocked_sync(ip: str, username: str) -> bool:
    """Check if IP or username is rate-limited. Fails open on Redis errors."""
    try:
        return redis_cache.run_sync(is_blocked(ip, username))
    except Exception as e:
        logger.warning("Rate-limit check failed (failing open): %s", e)
        return False


def record_login_failure_sync(ip: str, username: str, max_attempts: int = 5, window_seconds: int = 300) -> Tuple[int, bool]:
    """Record a failed login attempt. Fails silently on Redis errors."""
    try:
        return redis_cache.run_sync(record_login_failure(ip, username, max_attempts, window_seconds))
    except Exception as e:
        logger.warning("Failed to record login failure: %s", e)
        return (0, False)


def reset_login_failures_sync(ip: str, username: str):
    """Clear rate-limit counters after successful login. Fails silently."""
    try:
        redis_cache.run_sync(reset_login_failures(ip, username))
    except Exception as e:
        logger.warning("Failed to reset login failures: %s", e)
