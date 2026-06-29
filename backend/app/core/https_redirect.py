"""HTTPS redirect middleware.

When enabled, redirects all HTTP traffic to HTTPS using the configured
``HTTPS_REDIRECT_PORT`` (default 443).

Enabled by setting ``HTTPS_REDIRECT_ENABLED=true`` and ``HTTPS_REDIRECT_PORT``
in the environment.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.core.config import settings


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # BaseHTTPMiddleware breaks WebSocket upgrades — bypass early
        if request.scope.get("type") == "websocket":
            return await call_next(request)
        if not settings.HTTPS_REDIRECT_ENABLED:
            return await call_next(request)

        forwarded_proto = request.headers.get("x-forwarded-proto", "http")
        if forwarded_proto == "http":
            url = request.url.replace(scheme="https", port=settings.HTTPS_REDIRECT_PORT)
            return Response(status_code=301, headers={"location": str(url)})
        return await call_next(request)


def setup_https_redirect(app: FastAPI) -> None:
    app.add_middleware(HTTPSRedirectMiddleware)
