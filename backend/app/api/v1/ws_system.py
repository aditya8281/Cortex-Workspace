"""WebSocket endpoint for real-time system metrics."""

from __future__ import annotations

import asyncio
import json

import psutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.system_info import get_disk_info, get_gpu_info, get_ram_info

router = APIRouter()


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
        "gpu_percent": None,
        "disk_total_gb": disk["total_gb"],
        "disk_used_gb": disk["used_gb"],
        "disk_percent": disk["percent"],
    }


@router.websocket("/ws/system")
async def system_metrics_ws(ws: WebSocket):
    """Push system metrics every 2 seconds to connected clients."""
    await ws.accept()
    try:
        while True:
            metrics = collect_metrics()
            await ws.send_text(json.dumps(metrics))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
