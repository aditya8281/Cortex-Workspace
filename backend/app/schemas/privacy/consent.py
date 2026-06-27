"""Consent record schemas for API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConsentCreate(BaseModel):
    """Input schema for granting consent."""

    consent_type: str = Field(..., description="Data category: memory_read, file_write, etc.")
    scope: str | None = Field(None, description="Specific scope")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    expires_at: datetime | None = Field(None, description="Optional expiry")


class ConsentUpdate(BaseModel):
    """Input schema for updating consent."""

    granted: int | None = Field(None, description="1=granted, 0=denied")
    expires_at: datetime | None = None
    revoked_reason: str | None = None


class ConsentResponse(BaseModel):
    """Output schema for consent records."""

    id: int
    user_id: int
    consent_type: str
    granted: int
    scope: str | None = None
    context: dict[str, Any] | None = None
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    version: int

    model_config = {"from_attributes": True}
