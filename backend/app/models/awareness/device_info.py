"""Device info model — hardware and OS details per user."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class DeviceInfo(Base):
    """Device hardware and OS information."""

    __tablename__ = "device_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    os_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cpu_cores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpu_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_memory_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    available_memory_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disk_total_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disk_used_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    python_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_checked: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_device_user", "user_id", unique=True),
    )
