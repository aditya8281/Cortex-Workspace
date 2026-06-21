from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

MAX_CONNECTIONS_PER_CHANNEL = 100
MAX_MESSAGE_SIZE = 65536  # 64KB


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages."""

    def __init__(self) -> None:
        self.active: dict[str, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel: str = "default") -> None:
        channel_conns = self.active.get(channel, set())
        if len(channel_conns) >= MAX_CONNECTIONS_PER_CHANNEL:
            await ws.close(code=1013, reason="Too many connections")
            logger.warning("WebSocket connection rejected: channel '%s' full", channel)
            return
        await ws.accept()
        self.active.setdefault(channel, set()).add(ws)
        logger.info("WebSocket connected to channel '%s' (%d active)", channel, len(self.active[channel]))

    def disconnect(self, ws: WebSocket, channel: str = "default") -> None:
        self.active.get(channel, set()).discard(ws)
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
