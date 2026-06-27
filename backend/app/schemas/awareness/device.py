"""Device info Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DeviceInfoResponse(BaseModel):
    """Schema for returning device information."""

    id: int
    user_id: int
    hostname: str | None = None
    os_type: str | None = None
    os_version: str | None = None
    cpu_cores: int | None = None
    cpu_model: str | None = None
    total_memory_gb: int | None = None
    available_memory_gb: int | None = None
    disk_total_gb: int | None = None
    disk_used_gb: int | None = None
    python_version: str | None = None
    last_checked: datetime

    model_config = {"from_attributes": True}
