"""System metrics and logs endpoints."""

from __future__ import annotations

import psutil
from fastapi import APIRouter, Depends

from backend.app.api.deps import get_current_user
from backend.app.core.logging import get_recent_logs
from backend.app.core.system_info import get_disk_info, get_gpu_info, get_ram_info
from backend.app.models.user import User

router = APIRouter()


@router.get("/system/metrics")
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
):
    """Return real-time system metrics: CPU, RAM, GPU, Disk."""
    ram = get_ram_info()
    gpu = get_gpu_info()
    disk_path = current_user.storage_root if hasattr(current_user, 'storage_root') and current_user.storage_root else "."
    disk = get_disk_info(disk_path)

    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram_used = ram["total_gb"] - ram["available_gb"]

    return {
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


@router.get("/system/logs")
async def get_system_logs(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """Return recent system logs from the in-memory log buffer."""
    logs = get_recent_logs(limit=min(limit, 200))
    return {"logs": logs, "total": len(logs)}
