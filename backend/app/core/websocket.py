from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

MAX_CONNECTIONS_PER_CHANNEL = 100
MAX_CONNECTIONS_PER_USER = 10
MAX_MESSAGE_SIZE = 65536  # 64KB


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages."""

    @staticmethod
    def extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
        """Extract JWT from query param, sec-websocket-protocol header, or cookie."""
        if token:
            return token
        protocols = ws.headers.get("sec-websocket-protocol", "")
        if protocols:
            return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
        return ws.cookies.get("cortex_access")

    def __init__(self) -> None:
        self.active: dict[str, set[WebSocket]] = {}
        self._user_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel: str = "default", user_id: int | None = None) -> None:
        """Accept a new WebSocket connection and register it with the manager."""
        channel_conns = self.active.get(channel, set())
        if len(channel_conns) >= MAX_CONNECTIONS_PER_CHANNEL:
            await ws.close(code=1013, reason="Too many connections")
            logger.warning("WebSocket connection rejected: channel '%s' full", channel)
            return

        if user_id is not None:
            user_conns = self._user_connections.get(user_id, set())
            if len(user_conns) >= MAX_CONNECTIONS_PER_USER:
                await ws.close(code=1013, reason="Too many connections for user")
                logger.warning("WebSocket connection rejected: user %d exceeded limit", user_id)
                return

        await ws.accept()
        self._do_register(ws, channel, user_id)

    async def register(self, ws: WebSocket, channel: str = "default", user_id: int | None = None) -> None:
        """Register an already-accepted WebSocket without calling ws.accept() again.

        Use this with the accept-first pattern (accept → verify → register).
        """
        channel_conns = self.active.get(channel, set())
        if len(channel_conns) >= MAX_CONNECTIONS_PER_CHANNEL:
            await ws.close(code=1013, reason="Too many connections")
            logger.warning("WebSocket registration rejected: channel '%s' full", channel)
            return

        if user_id is not None:
            user_conns = self._user_connections.get(user_id, set())
            if len(user_conns) >= MAX_CONNECTIONS_PER_USER:
                await ws.close(code=1013, reason="Too many connections for user")
                logger.warning("WebSocket registration rejected: user %d exceeded limit", user_id)
                return

        self._do_register(ws, channel, user_id)

    def _do_register(self, ws: WebSocket, channel: str, user_id: int | None = None) -> None:
        """Internal: add a WebSocket to the tracking sets (accept must already have happened)."""
        self.active.setdefault(channel, set()).add(ws)
        if user_id is not None:
            self._user_connections.setdefault(user_id, set()).add(ws)
        logger.info("WebSocket registered on channel '%s' (%d active)", channel, len(self.active[channel]))

    def disconnect(self, ws: WebSocket, channel: str = "default", user_id: int | None = None) -> None:
        self.active.get(channel, set()).discard(ws)
        if user_id is not None:
            conns = self._user_connections.get(user_id, set())
            conns.discard(ws)
            if not conns:
                self._user_connections.pop(user_id, None)
        logger.info("WebSocket disconnected from channel '%s'", channel)

    async def send(self, ws: WebSocket, data: dict[str, Any]) -> None:
        try:
            text = json.dumps(data)
            if len(text) > MAX_MESSAGE_SIZE:
                logger.warning("WebSocket message too large (%d bytes), dropping", len(text))
                return
            await ws.send_text(text)
        except Exception:
            logger.exception("Failed to send WebSocket message")

    async def broadcast(self, channel: str, data: dict[str, Any]) -> None:
        text = json.dumps(data)
        if len(text) > MAX_MESSAGE_SIZE:
            logger.warning("WebSocket broadcast message too large (%d bytes), dropping", len(text))
            return
        dead: list[WebSocket] = []
        for ws in self.active.get(channel, set()):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, channel)


manager = ConnectionManager()
