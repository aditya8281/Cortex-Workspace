"""WebSocket endpoint for chat typing indicators and presence."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.db import verify_ws_token
from backend.app.core.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket, token: str = Query(None)):
    """Chat WebSocket — receives typing events, broadcasts to conversation channel.

    Client sends:
      {"action": "typing", "conversation_id": 123}
      {"action": "stop_typing", "conversation_id": 123}

    Server broadcasts to all OTHER connections on the same conversation channel:
      {"type": "typing", "conversation_id": 123, "user_id": 456}
      {"type": "stop_typing", "conversation_id": 123, "user_id": 456}
    """
    # Accept FIRST so the browser sees a 101 with CORS headers
    await ws.accept()

    token = manager.extract_ws_token(ws, token)  # type: ignore[assignment]
    if not token:
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close(code=4001)
        return
    try:
        user_id = await verify_ws_token(token)
    except Exception:
        await ws.send_json({"type": "error", "message": "Invalid token or account deleted"})
        await ws.close(code=4001)
        return

    uid = int(user_id)
    await manager.register(ws, channel="chat", user_id=uid)

    # Track which conversations this connection has joined
    joined_channels: set[str] = set()

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get("action")
            conv_id = msg.get("conversation_id")

            if action == "join" and conv_id is not None:
                channel = f"chat:{conv_id}"
                if channel not in joined_channels:
                    manager.active.setdefault(channel, set()).add(ws)
                    joined_channels.add(channel)

            elif action == "leave" and conv_id is not None:
                channel = f"chat:{conv_id}"
                manager.active.get(channel, set()).discard(ws)
                joined_channels.discard(channel)

            elif action in ("typing", "stop_typing") and conv_id is not None:
                channel = f"chat:{conv_id}"
                broadcast = {
                    "type": action,
                    "conversation_id": conv_id,
                    "user_id": uid,
                }
                # Send to everyone on this conversation channel EXCEPT the sender
                for other_ws in list(manager.active.get(channel, set())):
                    if other_ws is not ws:
                        try:
                            await manager.send(other_ws, broadcast)
                        except Exception:
                            manager.active.get(channel, set()).discard(other_ws)

            elif action == "ping":
                await manager.send(ws, {"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket chat error")
    finally:
        # Clean up from all joined channels
        for channel in joined_channels:
            manager.active.get(channel, set()).discard(ws)
        manager.disconnect(ws, channel="chat", user_id=uid)
