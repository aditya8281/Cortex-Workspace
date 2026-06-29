"""CORSMiddleware subclass that also adds CORS headers to WebSocket 101 responses.

Starlette's built-in CORSMiddleware bypasses scope["type"] != "http", which
means the WebSocket accept response (101 Switching Protocols) never gets
Access-Control-Allow-Origin headers. Browsers that enforce CORS on WebSocket
handshakes then block the connection.

This subclass intercepts WebSocket scopes, checks Origin against the allowed
list, and wraps `send` to inject CORS headers into the websocket.accept message.
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Receive, Scope, Send

logger = logging.getLogger(__name__)


class CORSMiddlewareWithWS(CORSMiddleware):
    """Extends Starlette CORSMiddleware to handle WebSocket CORS."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "websocket":
            # Normal HTTP path — delegate to Starlette's CORSMiddleware
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
            # Origin not allowed — reject the WebSocket connection
            await self.app(scope, receive, send)
            return

        # Origin is allowed — wrap send to inject CORS headers into the
        # websocket.accept message that ws.accept() produces.
        async def send_with_cors(message: MutableMapping[str, Any]) -> None:
            if message["type"] in ("websocket.accept", "websocket.close"):
                raw_headers: list[tuple[bytes, bytes]] = message.get("headers") or []

                # If credentials allowed, echo the specific origin (not *)
                if self.allow_all_origins and self.allow_credentials:
                    raw_headers.append((b"access-control-allow-origin", origin.encode()))
                    raw_headers.append((b"access-control-allow-credentials", b"true"))
                elif not self.allow_all_origins:
                    raw_headers.append((b"access-control-allow-origin", origin.encode()))

                message["headers"] = raw_headers

            await send(message)

        await self.app(scope, receive, send_with_cors)
