"""WebSocket endpoint for real-time model download progress."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.security import verify_access_token
from backend.app.services.model_downloader import model_downloader

router = APIRouter()


@router.websocket("/ws/models")
async def model_download_progress_ws(ws: WebSocket, token: str = Query(None)):
    """Push download progress for all active model downloads every second."""
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return
    await ws.accept()
    try:
        while True:
            active = model_downloader.get_active_progress()

            if active:
                payload = {
                    "type": "model_progress",
                    "models": [
                        {"name": name, "progress": prog}
                        for name, prog in active.items()
                    ],
                }
                await ws.send_text(json.dumps(payload))

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
