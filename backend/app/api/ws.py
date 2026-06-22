from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from backend.app.core.config import settings
from backend.app.core.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/demo")
async def websocket_demo(ws: WebSocket) -> None:
    # Accept token from sec-websocket-protocol header (preferred) or query param (legacy)
    token = None
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        # Token is sent as the first subprotocol
        token = protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    if not token:
        token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4001, reason="Missing authentication token")
        return
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            await ws.close(code=4001, reason="Invalid token")
            return
    except JWTError:
        await ws.close(code=4001, reason="Invalid token")
        return

    await manager.connect(ws, channel="demo")
    try:
        while True:
            raw = await ws.receive_text()
            msg: dict[str, Any] = json.loads(raw)
            action = msg.get("action", "echo")

            if action == "echo":
                await manager.send(ws, {"action": "echo", "data": msg.get("text", "")})

            elif action == "stream":
                text = msg.get("text", "Hello from Cortex!")
                words = text.split()
                if not words:
                    words = ["Hello", "from", "Cortex!"]
                for i, word in enumerate(words):
                    await asyncio.sleep(0.15)
                    await manager.send(
                        ws,
                        {
                            "action": "stream",
                            "chunk": word + (" " if i < len(words) - 1 else ""),
                            "index": i,
                            "done": False,
                        },
                    )
                await manager.send(ws, {"action": "stream", "chunk": "", "done": True})

            else:
                await manager.send(ws, {"action": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        manager.disconnect(ws, channel="demo")
    except Exception:
        logger.exception("WebSocket demo error")
        manager.disconnect(ws, channel="demo")
