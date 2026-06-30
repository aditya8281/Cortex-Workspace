"""WebSocket endpoint for real-time system metrics and activity logs."""

from __future__ import annotations

import asyncio
import logging

import psutil
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.db import verify_ws_token
from backend.app.core.logging import get_recent_logs
from backend.app.core.system_info import get_disk_info, get_gpu_info, get_ram_info
from backend.app.core.websocket import manager

logger = logging.getLogger(__name__)
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
                processes.append(
                    {
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu_percent": round(info["cpu_percent"], 1),
                        "memory_percent": round(info["memory_percent"], 1),
                    }
                )
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
    logger.info("[ws/system] Connection attempt from %s", ws.client)

    # Accept FIRST so the browser sees a 101 with CORS headers
    await ws.accept()

    token = manager.extract_ws_token(ws, token)  # type: ignore[assignment]
    if not token:
        logger.warning("[ws/system] No token provided")
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close(code=4001)
        return
    try:
        _user_id = await verify_ws_token(token)
    except Exception as e:
        logger.warning("[ws/system] Token verification failed: %s", e)
        await ws.send_json({"type": "error", "message": "Invalid token or account deleted"})
        await ws.close(code=4001)
        return
    uid = int(_user_id)
    logger.info("[ws/system] User %s connected", uid)
    await manager.register(ws, channel=f"system:{uid}", user_id=uid)
    tick = 0
    try:
        while True:
            tick += 1
            metrics = collect_metrics()
            await manager.send(ws, metrics)

            if tick % 6 == 1:
                logs = collect_logs(15)
                await manager.send(ws, logs)

            if tick % 10 == 0:
                processes = collect_processes()
                await manager.send(ws, {"type": "processes", "processes": processes})

            # Probe for disconnect every 60 ticks (~30s)
            if tick % 60 == 0 and await manager.check_disconnected(ws):
                logger.info("[ws/system] Client disconnected (probe), user %s", uid)
                break

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
    finally:
        manager.disconnect(ws, channel=f"system:{uid}", user_id=uid)
