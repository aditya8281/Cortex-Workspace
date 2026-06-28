"""ErrorAnalysis schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorAnalysisCreate(BaseModel):
    error_type: str = Field(..., description="Error class name")
    error_message: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"


class ErrorAnalysisUpdate(BaseModel):
    root_cause: str | None = None
    resolution: str | None = None
    prevention: str | None = None
    severity: str | None = None
    resolved: int | None = None
    resolution_method: str | None = None


class ErrorAnalysisResponse(BaseModel):
    id: int
    user_id: int
    error_type: str
    error_message: str | None = None
    fingerprint: str | None = None
    context: dict[str, Any] | None = None
    root_cause: str | None = None
    resolution: str | None = None
    prevention: str | None = None
    severity: str
    resolved: int
    resolution_method: str | None = None
    related_analysis_id: int | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class ErrorAnalysisListResponse(BaseModel):
    items: list[ErrorAnalysisResponse]
    total: int
