from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.core.config import settings
from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting middleware using Redis sliding window.

    Configured via ``RATE_LIMIT_REQUESTS`` and ``RATE_LIMIT_WINDOW_SECONDS``
    environment variables (see ``backend.app.core.config.Settings``).
    """

    def __init__(self, app: ASGIApp, max_requests: int | None = None, window: int | None = None):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window = window or settings.RATE_LIMIT_WINDOW_SECONDS

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith(("/api/v1/health", "/metrics")):
            return await call_next(request)

        is_auth_endpoint = request.url.path.startswith("/api/v1/auth")
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{'auth:' if is_auth_endpoint else ''}{client_ip}"

        try:
            current = await redis_cache.get(key) or {"count": 0, "window_start": time.time()}
            if time.time() - current["window_start"] > self.window:
                current = {"count": 0, "window_start": time.time()}
            current["count"] += 1
            await redis_cache.set(key, current, expire_seconds=self.window)

            max_req = min(self.max_requests, 10) if is_auth_endpoint else self.max_requests
            if current["count"] > max_req:
                return Response(status_code=429, content="Rate limit exceeded")
        except Exception as e:
            logger.warning("Rate limiter Redis failure for %s %s: %s", request.method, request.url.path, e)
            return await call_next(request)

        return await call_next(request)


def setup_rate_limiting(app: FastAPI) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    app.add_middleware(RateLimitMiddleware)
