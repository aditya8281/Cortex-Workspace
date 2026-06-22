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


def collect_processes(n: int = 5) -> list[dict]:
    """Collect top N processes by CPU usage."""
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            if info["cpu_percent"] and info["cpu_percent"] > 0:
                processes.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu_percent": round(info["cpu_percent"], 1),
                    "memory_percent": round(info["memory_percent"], 1)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return processes[:n]


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
    """Push real-time metrics (every 500ms) and activity logs (every 3s)."""
    # Accept token from sec-websocket-protocol header (preferred) or query param (legacy)
    if not token:
        protocols = ws.headers.get("sec-websocket-protocol", "")
        if protocols:
            token = protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        _user_id = verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return
    await ws.accept()
    tick = 0
    try:
        while True:
            tick += 1
            # Metrics: every iteration (500ms)
            metrics = collect_metrics()
            await ws.send_text(json.dumps(metrics))

            # Logs: every ~3 seconds (every 6th tick)
            if tick % 6 == 1:
                logs = collect_logs(15)
                await ws.send_text(json.dumps(logs))

            # Processes: every ~5 seconds (every 10th tick) - heavier operation
            if tick % 10 == 0:
                processes = collect_processes()
                await ws.send_text(json.dumps({"type": "processes", "processes": processes}))

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
