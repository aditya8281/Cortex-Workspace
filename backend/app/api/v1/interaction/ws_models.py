"""WebSocket endpoint for real-time model download progress."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.db import verify_ws_token
from backend.app.core.websocket import manager
from backend.app.services.download.downloader import DownloadStatus, download_manager

router = APIRouter()


def _build_download_payload() -> dict:
    """Build the full model_progress payload from DownloadManager records."""
    models = []
    queued_positions: dict[str, int] = {}
    position_counter = 1
    for rec in download_manager._records.values():
        if rec.status == DownloadStatus.QUEUED:
            queued_positions[rec.download_id] = position_counter
            position_counter += 1

    for rec in download_manager._records.values():
        if rec.status in (
            DownloadStatus.DOWNLOADING,
            DownloadStatus.QUEUED,
            DownloadStatus.PAUSED,
        ):
            models.append(
                {
                    "name": rec.model_name,
                    "progress": rec.progress,
                    "status": rec.status.value,
                    "speed_bytes_sec": rec.speed_bytes_sec,
                    "eta_seconds": rec.eta_seconds,
                    "bytes_downloaded": rec.bytes_downloaded,
                    "total_bytes": rec.total_bytes,
                    "queue_position": queued_positions.get(rec.download_id),
                    "download_id": rec.download_id,
                }
            )
        elif rec.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            models.append(
                {
                    "name": rec.model_name,
                    "progress": rec.progress,
                    "status": rec.status.value,
                    "speed_bytes_sec": 0,
                    "eta_seconds": None,
                    "bytes_downloaded": rec.bytes_downloaded,
                    "total_bytes": rec.total_bytes,
                    "queue_position": None,
                    "download_id": rec.download_id,
                    "error": rec.error_message,
                }
            )

    return {"type": "model_progress", "models": models}


@router.websocket("/ws/models")
async def model_download_progress_ws(ws: WebSocket, token: str = Query(None)):
    """Push download progress for all active model downloads every second."""
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
    await manager.register(ws, channel=f"models:{uid}", user_id=uid)
    try:
        while True:
            payload = _build_download_payload()
            if payload["models"]:
                await manager.send(ws, payload)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
    finally:
        manager.disconnect(ws, channel=f"models:{uid}", user_id=uid)
