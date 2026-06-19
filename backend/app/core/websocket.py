from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages."""

    def __init__(self) -> None:
        self.active: dict[str, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel: str = "default") -> None:
        await ws.accept()
        self.active.setdefault(channel, set()).add(ws)
        logger.info("WebSocket connected to channel '%s' (%d active)", channel, len(self.active[channel]))

    def disconnect(self, ws: WebSocket, channel: str = "default") -> None:
        self.active.get(channel, set()).discard(ws)
        logger.info("WebSocket disconnected from channel '%s'", channel)

    async def send(self, ws: WebSocket, data: dict[str, Any]) -> None:
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            logger.exception("Failed to send WebSocket message")

    async def broadcast(self, channel: str, data: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.active.get(channel, set()):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, channel)


manager = ConnectionManager()
