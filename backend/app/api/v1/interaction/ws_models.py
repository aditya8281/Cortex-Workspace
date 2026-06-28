"""WebSocket endpoint for real-time model download progress."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.security import verify_access_token
from backend.app.services.download.downloader import DownloadStatus, download_manager

router = APIRouter()


def _extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    """Extract JWT from query param, sec-websocket-protocol header, or cookie."""
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")


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
            models.append({
                "name": rec.model_name,
                "progress": rec.progress,
                "status": rec.status.value,
                "speed_bytes_sec": rec.speed_bytes_sec,
                "eta_seconds": rec.eta_seconds,
                "bytes_downloaded": rec.bytes_downloaded,
                "total_bytes": rec.total_bytes,
                "queue_position": queued_positions.get(rec.download_id),
                "download_id": rec.download_id,
            })
        elif rec.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            models.append({
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
            })

    return {"type": "model_progress", "models": models}


@router.websocket("/ws/models")
async def model_download_progress_ws(ws: WebSocket, token: str = Query(None)):
    """Push download progress for all active model downloads every second."""
    token = _extract_ws_token(ws, token)
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        _user_id = verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return
    await ws.accept()
    try:
        while True:
            payload = _build_download_payload()

            if payload["models"]:
                await ws.send_text(json.dumps(payload))

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
