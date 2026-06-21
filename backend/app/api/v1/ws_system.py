"""WebSocket endpoint for real-time system metrics and activity logs."""

from __future__ import annotations

import asyncio
import json

import psutil
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.logging import get_recent_logs
from backend.app.core.security import verify_access_token
from backend.app.core.system_info import get_disk_info, get_gpu_info, get_ram_info

router = APIRouter()


# ── Metrics ──────────────────────────────────────────────────────────


def collect_metrics() -> dict:
    """Collect current system metrics."""
    ram = get_ram_info()
    gpu = get_gpu_info()
    disk = get_disk_info(".")
    cpu_percent = psutil.cpu_percent(interval=0)
    ram_used = ram["total_gb"] - ram["available_gb"]

    return {
        "type": "metrics",
        "cpu_percent": cpu_percent,
        "ram_total_gb": ram["total_gb"],
        "ram_used_gb": round(ram_used, 2),
        "ram_percent": round((ram_used / ram["total_gb"]) * 100, 1) if ram["total_gb"] > 0 else 0,
        "gpu_name": gpu.get("name", "No GPU detected"),
        "gpu_type": gpu.get("type", ""),
        "gpu_percent": gpu.get("utilization_gpu") if gpu.get("detected") else None,
        "disk_total_gb": disk["total_gb"],
        "disk_used_gb": disk["used_gb"],
        "disk_percent": disk["percent"],
    }


# ── Logs ─────────────────────────────────────────────────────────────


def collect_logs(n: int = 15) -> dict:
    """Collect recent system activity logs."""
    logs = get_recent_logs(limit=n)
    return {
        "type": "logs",
        "logs": logs,
        "total": len(logs),
    }


# ── WebSocket ────────────────────────────────────────────────────────


@router.websocket("/ws/system")
async def system_metrics_ws(ws: WebSocket, token: str = Query(None)):
    """Push real-time metrics (every 2s) and activity logs (every 5s)."""
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return
    await ws.accept()
    tick = 0
    try:
        while True:
            tick += 1
            # Metrics: every iteration (2s)
            metrics = collect_metrics()
            await ws.send_text(json.dumps(metrics))

            # Logs: every ~6 seconds (every 3rd tick; tick 1 covers cold-start)
            if tick % 3 == 1:
                logs = collect_logs(15)
                await ws.send_text(json.dumps(logs))

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
