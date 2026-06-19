import json
import logging
from typing import Any

import redis.asyncio as aioredis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Async Redis caching client with graceful degradation if Redis is down.
    """
    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.client: aioredis.Redis | None = None
        self._connected: bool = False

    def get_client(self) -> aioredis.Redis:
        if self.client is None:
            self.client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
        return self.client

    async def ping(self) -> bool:
        try:
            client = self.get_client()
            await client.ping()
            self._connected = True
            return True
        except Exception as e:
            logger.warning("Redis is unavailable at %s: %s", self.redis_url, e)
            self._connected = False
            return False

    async def get(self, key: str) -> Any | None:
        try:
            client = self.get_client()
            val = await client.get(key)
            if val is not None:
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return val
            return None
        except Exception as e:
            logger.warning("Failed to GET from Redis key %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, expire_seconds: int | None = None) -> bool:
        try:
            client = self.get_client()
            serialized_value = json.dumps(value)
            await client.set(key, serialized_value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.warning("Failed to SET to Redis key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = self.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning("Failed to DELETE from Redis key %s: %s", key, e)
            return False

    async def info(self, section: str | None = None) -> dict[str, Any] | None:
        try:
            client = self.get_client()
            if section:
                return await client.info(section)
            return await client.info()
        except Exception as e:
            logger.warning("Failed to read Redis info: %s", e)
            return None

    async def clear_pattern(self, pattern: str) -> bool:
        try:
            client = self.get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.warning("Failed to clear pattern %s in Redis: %s", pattern, e)
            return False

    async def close(self):
        if self.client is not None:
            try:
                await self.client.aclose()
            except (RuntimeError, OSError, Exception):
                pass  # event loop already closed or connection already lost
            self.client = None
            self._connected = False



# Global redis cache instance
redis_cache = RedisCache()
