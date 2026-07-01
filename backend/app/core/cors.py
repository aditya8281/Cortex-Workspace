"""CORSMiddleware subclass that also adds CORS headers to WebSocket 101 responses.

Starlette's built-in CORSMiddleware bypasses scope["type"] != "http", which
means the WebSocket accept response (101 Switching Protocols) never gets
Access-Control-Allow-Origin headers. Browsers that enforce CORS on WebSocket
handshakes then block the connection.

This subclass intercepts WebSocket scopes, checks Origin against the allowed
list, and wraps `send` to inject CORS headers into the websocket.accept message.

In dev mode (ENV=development), any localhost:PORT origin is accepted since
start.sh assigns ports dynamically.
"""

from __future__ import annotations

import logging
import re
from collections.abc import MutableMapping
from typing import Any

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Receive, Scope, Send

logger = logging.getLogger(__name__)

# Match http://localhost:PORT or http://127.0.0.1:PORT
_LOCALHOST_PATTERN = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


class CORSMiddlewareWithWS(CORSMiddleware):
    """Extends Starlette CORSMiddleware to handle WebSocket CORS.

    In dev mode, accepts any localhost origin (ports are dynamic).
    """

    def __init__(self, app: Any, **kwargs: Any) -> None:
        super().__init__(app, **kwargs)
        # Capture dev-mode flag from settings
        from backend.app.core.config import settings

        self.dev_accept_any_localhost: bool = getattr(settings, "_dev_accept_any_localhost", False)

    def is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed — also match any localhost in dev."""
        return (
            super().is_allowed_origin(origin)
            or (self.dev_accept_any_localhost and _LOCALHOST_PATTERN.match(origin) is not None)
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "websocket":
            await super().__call__(scope, receive, send)
            return

        # ── WebSocket path ───────────────────────────────────────────────
        headers = Headers(scope=scope)
        origin = headers.get("origin")
        logger.info("[cors-ws] WS scope path=%s origin=%s", scope.get("path"), origin)

        # No origin → same-origin or non-browser client — pass through
        if origin is None:
            await self.app(scope, receive, send)
            return

        # Check if origin is allowed
        if not self.allow_all_origins and not self.is_allowed_origin(origin=origin):
            logger.warning("[cors-ws] REJECTED origin=%s allowed=%s", origin, self.allow_origins)
            await self.app(scope, receive, send)
            return

        # Capture the client-requested subprotocol so we can echo it back.
        # Browsers REQUIRE the server to echo the subprotocol in the 101
        # accept response — without this, every WS connection silently fails.
        requested_protocol = Headers(scope=scope).get("sec-websocket-protocol", "").strip()

        # Origin is allowed — wrap send to inject CORS headers into the
        # websocket.accept message that ws.accept() produces.
        async def send_with_cors(message: MutableMapping[str, Any]) -> None:
            if message["type"] in ("websocket.accept", "websocket.close"):
                raw_headers: list[tuple[bytes, bytes]] = message.get("headers") or []

                origin_header = origin.encode()
                raw_headers.append((b"access-control-allow-origin", origin_header))
                if self.allow_credentials:
                    raw_headers.append((b"access-control-allow-credentials", b"true"))

                message["headers"] = raw_headers

                # Echo back the requested subprotocol (required by browsers)
                if message["type"] == "websocket.accept" and requested_protocol:
                    message["subprotocol"] = requested_protocol

            await send(message)

        await self.app(scope, receive, send_with_cors)
