"""Device awareness API — hardware and OS information."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.services.awareness.device_service import DeviceInfoService

router = APIRouter(prefix="/device", tags=["awareness-device"])


@router.get("/info", response_model=dict[str, Any])
def get_device_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current device hardware and OS information."""
    service = DeviceInfoService(db)
    device = service.get_device_info(current_user.id)
    return {
        "id": device.id,
        "hostname": device.hostname,
        "os_type": device.os_type,
        "os_version": device.os_version,
        "cpu_cores": device.cpu_cores,
        "cpu_model": device.cpu_model,
        "total_memory_gb": device.total_memory_gb,
        "available_memory_gb": device.available_memory_gb,
        "disk_total_gb": device.disk_total_gb,
        "disk_used_gb": device.disk_used_gb,
        "python_version": device.python_version,
        "last_checked": device.last_checked.isoformat() if device.last_checked else None,
    }
