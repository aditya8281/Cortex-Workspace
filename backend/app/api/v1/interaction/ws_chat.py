"""WebSocket endpoint for chat typing indicators and presence."""

from __future__ import annotations

import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.security import verify_access_token
from backend.app.core.websocket import manager

router = APIRouter()


def _extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    """Extract JWT from query param, sec-websocket-protocol header, or cookie."""
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")


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
    token = _extract_ws_token(ws, token)
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        user_id = verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return

    uid = int(user_id)
    await manager.connect(ws, channel="chat", user_id=uid)

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
        pass
    finally:
        # Clean up from all joined channels
        for channel in joined_channels:
            manager.active.get(channel, set()).discard(ws)
        manager.disconnect(ws, channel="chat", user_id=uid)
