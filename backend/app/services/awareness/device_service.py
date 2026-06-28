"""Device info service — collects hardware and OS details per user."""

from __future__ import annotations

import os
import platform
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.awareness.device_info import DeviceInfo

# Try to import psutil (optional)
try:
    import psutil as _psutil
except ImportError:
    _psutil = None  # type: ignore[assignment]


class DeviceInfoService:
    """Device hardware and OS information service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_device_info(self, user_id: int) -> DeviceInfo:
        """Get or create device information for *user_id*.

        Performs upsert: updates existing record or creates new one.
        """
        hostname = platform.node()
        os_type = platform.system().lower()
        os_version = platform.version()
        python_version = platform.python_version()

        cpu_cores = self._get_cpu_cores()
        cpu_model = self._get_cpu_model()
        total_memory_gb = self._get_total_memory()
        available_memory_gb = self._get_available_memory()
        disk_total_gb = self._get_disk_total()
        disk_used_gb = self._get_disk_used()

        existing = self.db.query(DeviceInfo).filter(DeviceInfo.user_id == user_id).first()

        if existing is not None:
            existing.hostname = hostname
            existing.os_type = os_type
            existing.os_version = os_version
            existing.python_version = python_version
            existing.cpu_cores = cpu_cores
            existing.cpu_model = cpu_model
            existing.total_memory_gb = total_memory_gb
            existing.available_memory_gb = available_memory_gb
            existing.disk_total_gb = disk_total_gb
            existing.disk_used_gb = disk_used_gb
            existing.last_checked = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        device = DeviceInfo(
            user_id=user_id,
            hostname=hostname,
            os_type=os_type,
            os_version=os_version,
            python_version=python_version,
            cpu_cores=cpu_cores,
            cpu_model=cpu_model,
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            last_checked=datetime.now(),
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_cpu_cores(self) -> int | None:
        """Get CPU core count."""
        if _psutil is not None:
            return _psutil.cpu_count(logical=True)  # type: ignore[union-attr]
        return os.cpu_count()

    def _get_cpu_model(self) -> str | None:
        """Get CPU model name."""
        return platform.processor() or None

    def _get_total_memory(self) -> int:
        """Get total memory in GB."""
        if _psutil is not None:
            return _psutil.virtual_memory().total // (1024**3)  # type: ignore[union-attr]
        return 0

    def _get_available_memory(self) -> int:
        """Get available memory in GB."""
        if _psutil is not None:
            return _psutil.virtual_memory().available // (1024**3)  # type: ignore[union-attr]
        return 0

    def _get_disk_total(self) -> int:
        """Get total disk in GB."""
        if _psutil is not None:
            return _psutil.disk_usage("/").total // (1024**3)  # type: ignore[union-attr]
        return 0

    def _get_disk_used(self) -> int:
        """Get used disk in GB."""
        if _psutil is not None:
            return _psutil.disk_usage("/").used // (1024**3)  # type: ignore[union-attr]
        return 0
