"""System resource snapshot for monitoring."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class SystemSnapshot(Base):
    __tablename__ = "system_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # CPU & memory
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)
    memory_percent: Mapped[float] = mapped_column(Float, nullable=False)
    memory_used_gb: Mapped[float] = mapped_column(Float, nullable=False)
    memory_total_gb: Mapped[float] = mapped_column(Float, nullable=False)

    # Disk
    disk_percent: Mapped[float] = mapped_column(Float, nullable=False)
    disk_used_gb: Mapped[float] = mapped_column(Float, nullable=False)
    disk_total_gb: Mapped[float] = mapped_column(Float, nullable=False)

    # GPU (optional)
    gpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_memory_used_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_memory_total_gb: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Network
    network_sent_bytes: Mapped[int] = mapped_column(Integer, default=0)
    network_recv_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Load averages
    load_average_1m: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_average_5m: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_average_15m: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Process info
    process_count: Mapped[int] = mapped_column(Integer, default=0)
    uptime_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
