from __future__ import annotations

import logging
import time

from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)

FAIL_PREFIX = "auth_fail:"  # keyed by ip:username
BLOCK_PREFIX = "auth_block:"  # keyed by ip or username

# Timeout for Redis operations during auth — fail open if exceeded
REDIS_AUTH_TIMEOUT = 3.0


# ── Async versions (used by background tasks) ─────────────────────────

async def record_login_failure(ip: str, username: str, max_attempts: int = 5, window_seconds: int = 300) -> tuple[int, bool]:
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
    """Check if IP or username is rate-limited. Always fails open —
    Redis rate-limiting is only enforced via the async endpoints.
    The sync path cannot safely use redis_cache.run_sync() because it
    creates a new event loop that deadlocks with the shared aioredis client.
    """
    return False


def record_login_failure_sync(ip: str, username: str, max_attempts: int = 5, window_seconds: int = 300) -> tuple[int, bool]:
    """Record a failed login attempt. No-op in sync path — see is_blocked_sync."""
    return (0, False)


def reset_login_failures_sync(ip: str, username: str):
    """Clear rate-limit counters. No-op in sync path — see is_blocked_sync."""
    return
