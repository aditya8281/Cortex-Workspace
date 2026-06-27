"""Tests for v1.04 P03 device info service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.services.awareness.device_service import DeviceInfoService


class TestDeviceInfoService:
    def test_get_device_info(self, db_session: Session) -> None:
        """Getting device information returns valid data."""
        service = DeviceInfoService(db_session)
        device = service.get_device_info(user_id=1)

        assert device.hostname is not None
        assert device.os_type in ("linux", "darwin", "windows")
        assert device.python_version is not None
        assert device.cpu_cores is not None
        assert device.cpu_cores >= 1

    def test_device_upsert(self, db_session: Session) -> None:
        """Re-checking updates existing record (upsert)."""
        service = DeviceInfoService(db_session)
        d1 = service.get_device_info(user_id=1)
        first_id = d1.id

        d2 = service.get_device_info(user_id=1)
        assert d2.id == first_id

    def test_device_user_isolation(self, db_session: Session) -> None:
        """Device info is isolated by user_id."""
        service = DeviceInfoService(db_session)
        d1 = service.get_device_info(user_id=1)
        d2 = service.get_device_info(user_id=2)

        assert d1.id != d2.id
        assert d1.user_id == 1
        assert d2.user_id == 2

    def test_device_has_memory_info(self, db_session: Session) -> None:
        """Device info includes memory data (may be 0 without psutil)."""
        service = DeviceInfoService(db_session)
        device = service.get_device_info(user_id=1)

        assert device.total_memory_gb is not None
        assert device.total_memory_gb >= 0

    def test_device_has_disk_info(self, db_session: Session) -> None:
        """Device info includes disk data (may be 0 without psutil)."""
        service = DeviceInfoService(db_session)
        device = service.get_device_info(user_id=1)

        assert device.disk_total_gb is not None
        assert device.disk_total_gb >= 0

    def test_device_os_version_populated(self, db_session: Session) -> None:
        """Device info includes OS version string."""
        service = DeviceInfoService(db_session)
        device = service.get_device_info(user_id=1)

        assert device.os_version is not None
        assert len(device.os_version) > 0

    def test_multiple_users_get_different_records(self, db_session: Session) -> None:
        """Each user gets their own device info record."""
        service = DeviceInfoService(db_session)
        records = []
        for uid in range(1, 5):
            records.append(service.get_device_info(user_id=uid))

        ids = [r.id for r in records]
        assert len(set(ids)) == 4
