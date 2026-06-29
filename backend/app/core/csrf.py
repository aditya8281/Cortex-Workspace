"""CSRF protection via double-submit cookie pattern.

On every GET request, sets a ``cortex_csrf`` cookie (non-httpOnly, readable
by JavaScript). State-changing requests (POST, PUT, DELETE, PATCH) must include
the token in an ``X-CSRF-Token`` header matching the cookie value.

Endpoints under ``/api/auth/`` and ``/api/v1/health/``
are exempt. Auth endpoints are API-client-facing.
"""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.core.config import settings

CSRF_COOKIE_NAME = "cortex_csrf"
CSRF_HEADER_NAME = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/v1/health/", "/metrics", "/ws", "/api/v1/ws")


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # BaseHTTPMiddleware breaks WebSocket upgrades — bypass early
        if request.scope.get("type") == "websocket":
            return await call_next(request)
        if any(request.url.path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        # Requests with a Bearer token are API calls, not browser form submissions
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return await call_next(request)

        if request.method in SAFE_METHODS:
            response = await call_next(request)
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                httponly=False,
                samesite="lax",
                secure=settings.ENV not in ("development", "test"),
                path="/",
                max_age=3600,
            )
            return response

        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return Response(status_code=403, content="CSRF validation failed")
        return await call_next(request)


def setup_csrf_protection(app: FastAPI) -> None:
    app.add_middleware(CSRFMiddleware)
