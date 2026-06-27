"""Audit log schemas for API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """Input schema for creating audit log entries."""

    action: str = Field(..., description="Action type: create, read, update, delete, login, logout")
    resource_type: str = Field(..., description="Resource domain: memory, file, settings, agent")
    resource_id: int | None = Field(None, description="ID of affected resource")
    details: dict[str, Any] | None = Field(None, description="Additional context")
    ip_address: str | None = Field(None, description="Client IP")
    user_agent: str | None = Field(None, description="Client user agent")
    session_id: str | None = Field(None, description="Session ID")
    success: int = Field(1, description="1=success, 0=failure")
    error_message: str | None = Field(None, description="Error if failed")
    duration_ms: int | None = Field(None, description="Action duration in ms")


class AuditLogResponse(BaseModel):
    """Output schema for audit log entries."""

    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: int | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    timestamp: datetime
    success: int
    error_message: str | None = None
    duration_ms: int | None = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
