"""Demo WebSocket endpoint for manual development testing.

Usage:
  1. Obtain a valid JWT token from your local CORTEX instance.
  2. Connect via a WebSocket client (e.g., wscat, Postman):
     wscat -c ws://localhost:8000/ws/demo -H "sec-websocket-protocol: <token>"
  3. Send JSON messages with actions: "echo", "stream", or custom.

This endpoint is NOT used by any frontend page — it exists solely for
ad-hoc testing of the WebSocket infrastructure (auth, streaming, lifecycle).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.db import verify_ws_token
from backend.app.core.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/demo")
async def websocket_demo(ws: WebSocket) -> None:
    # Accept FIRST so the browser sees a 101 with CORS headers
    await ws.accept()

    # Accept token from sec-websocket-protocol header (preferred), query param (legacy), or cookie
    token = manager.extract_ws_token(ws) or ws.query_params.get("token")
    if not token:
        await ws.send_json({"type": "error", "message": "Missing authentication token"})
        await ws.close(code=4001)
        return
    try:
        user_id = await verify_ws_token(token)
    except Exception:
        await ws.send_json({"type": "error", "message": "Invalid token or account deleted"})
        await ws.close(code=4001)
        return

    await manager.register(ws, channel="demo")
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
