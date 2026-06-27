"""System health Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Schema for returning a health check result."""

    id: int
    service_name: str
    status: str
    response_time_ms: int | None = None
    error_message: str | None = None
    check_details: str | None = None
    last_check: datetime

    model_config = {"from_attributes": True}


class SystemHealthResponse(BaseModel):
    """Schema for returning all health checks."""

    services: list[HealthCheckResponse]
    overall_status: str
    checked_at: datetime
