"""WebSocket endpoint for real-time notifications."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select

from backend.app.core.security import verify_access_token
from backend.app.core.websocket import manager
from backend.app.db.session import SessionLocal
from backend.app.models.interaction.notification import Notification

router = APIRouter()


def _extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    """Extract JWT from query param, sec-websocket-protocol header, or cookie."""
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")


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
    token = _extract_ws_token(ws, token)
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        user_id = verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return

    await manager.connect(ws, channel=f"notifications:{user_id}", user_id=int(user_id))
    try:
        while True:
            try:
                data = _fetch_notifications(user_id)
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
