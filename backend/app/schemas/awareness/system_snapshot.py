"""System snapshot Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SystemSnapshotCreate(BaseModel):
    """Schema for creating a system snapshot."""

    user_id: int | None = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    gpu_percent: float | None = None
    gpu_memory_used_gb: float | None = None
    gpu_memory_total_gb: float | None = None
    network_sent_bytes: int = 0
    network_recv_bytes: int = 0
    load_average_1m: float | None = None
    load_average_5m: float | None = None
    load_average_15m: float | None = None
    process_count: int = 0
    uptime_seconds: float = 0.0
    meta: dict = {}


class SystemSnapshotResponse(SystemSnapshotCreate):
    """Schema for returning a system snapshot."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemSnapshotListResponse(BaseModel):
    """Schema for returning a list of system snapshots."""

    snapshots: list[SystemSnapshotResponse]
    total: int
