"""System metrics and logs endpoints."""

from __future__ import annotations

import psutil
from fastapi import APIRouter

from backend.app.core.logging import get_recent_logs
from backend.app.core.system_info import get_disk_info, get_gpu_info, get_ram_info

router = APIRouter()


def _get_top_processes(n: int = 20) -> list[dict]:
    """Return top N processes by CPU usage."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu": round(info["cpu_percent"] or 0.0, 1),
                "memory": round(info["memory_percent"] or 0.0, 1),
                "status": "running" if info["status"] == psutil.STATUS_RUNNING else "sleeping",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:n]


@router.get("/system/metrics")
async def get_system_metrics():
    """Return real-time system metrics: CPU, RAM, GPU, Disk, Processes.

    Public endpoint — system info is not user-specific and does not
    require authentication.
    """
    ram = get_ram_info()
    gpu = get_gpu_info()
    disk = get_disk_info(".")

    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram_used = ram["total_gb"] - ram["available_gb"]

    return {
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
        "processes": _get_top_processes(20),
    }


@router.get("/system/logs")
async def get_system_logs(
    limit: int = 20,
):
    """Return recent system logs from the in-memory log buffer.

    Public endpoint — system logs are not user-specific.
    """
    logs = get_recent_logs(limit=min(limit, 200))
    return {"logs": logs, "total": len(logs)}
