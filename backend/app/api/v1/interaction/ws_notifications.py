"""WebSocket endpoint for real-time notifications."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select

from backend.app.core.db import verify_ws_token
from backend.app.core.websocket import manager
from backend.app.db.session import SessionLocal
from backend.app.models.interaction.notification import Notification

router = APIRouter()



def _fetch_notifications(user_id: str) -> dict:
    """Fetch unread notifications for a user."""
    db = SessionLocal()
    try:
        count_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == int(user_id))
            .where(Notification.read == False)  # noqa: E712
        )
        result = db.execute(count_stmt)
        unread = result.scalar() or 0

        stmt = (
            select(Notification)
            .where(Notification.user_id == int(user_id))
            .where(Notification.read == False)  # noqa: E712
            .order_by(Notification.created_at.desc())
            .limit(5)
        )
        result = db.execute(stmt)
        rows = result.scalars().all()

        return {
            "type": "notifications",
            "unread_count": unread,
            "notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "type": n.type,
                    "created_at": str(n.created_at),
                }
                for n in rows
            ],
        }
    finally:
        db.close()


@router.websocket("/ws/notifications")
async def notifications_ws(ws: WebSocket, token: str = Query(None)):
    """Push new notifications to the connected user every 10 seconds."""
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

    await manager.register(ws, channel=f"notifications:{user_id}", user_id=int(user_id))
    try:
        while True:
            try:
                data = _fetch_notifications(str(user_id))
            except Exception:
                data = {"type": "notifications", "unread_count": 0, "notifications": []}
            await manager.send(ws, data)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(ws, channel=f"notifications:{user_id}", user_id=int(user_id))
