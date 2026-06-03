import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Async Redis caching client with graceful degradation if Redis is down.
    """
    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None
        self._connected: bool = False

    def get_client(self) -> aioredis.Redis:
        if self.client is None:
            # Create connection pool client
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
            logger.warning(f"Redis is unavailable at {self.redis_url}: {e}")
            self._connected = False
            return False

    async def get(self, key: str) -> Optional[Any]:
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
            logger.warning(f"Failed to GET from Redis key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        try:
            client = self.get_client()
            serialized_value = json.dumps(value)
            await client.set(key, serialized_value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.warning(f"Failed to SET to Redis key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = self.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to DELETE from Redis key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> bool:
        try:
            client = self.get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Failed to clear pattern {pattern} in Redis: {e}")
            return False

    async def close(self):
        if self.client is not None:
            await self.client.aclose()
            self.client = None
            self._connected = False


# Global redis cache instance
redis_cache = RedisCache()
