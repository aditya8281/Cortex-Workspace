"""Data export schemas for API contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExportCreate(BaseModel):
    """Input schema for data export request."""

    export_type: str = Field("full", description="full or partial")
    data_types: list[str] | None = Field(None, description="Specific types for partial export")
    format: str = Field("json", description="json or csv")


class ExportResponse(BaseModel):
    """Output schema for data export."""

    id: int
    user_id: int
    export_type: str
    data_types: list[str] | None = None
    format: str
    status: str
    file_path: str | None = None
    file_size_bytes: int | None = None
    checksum_sha256: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}
