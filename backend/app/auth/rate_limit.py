from __future__ import annotations

from typing import Tuple
import time

from backend.app.core.redis import redis_cache

FAIL_PREFIX = "auth_fail:"  # keyed by ip:username
BLOCK_PREFIX = "auth_block:"  # keyed by ip or username


async def record_login_failure(ip: str, username: str, max_attempts: int = 5, window_seconds: int = 300) -> Tuple[int, bool]:
    key = f"{FAIL_PREFIX}{ip}:{username}"
    val = await redis_cache.get(key) or {"count": 0, "first": time.time()}
    val["count"] = val.get("count", 0) + 1
    await redis_cache.set(key, val, expire_seconds=window_seconds)
    blocked = val["count"] >= max_attempts
    if blocked:
        # set block for ip and username for a temporary lockout
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
