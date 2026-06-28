"""ConfidenceScore schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConfidenceEstimate(BaseModel):
    task_type: str = Field(..., description="Task type to estimate confidence for")
    context: dict[str, Any] | None = None


class ConfidenceResponse(BaseModel):
    task_type: str
    confidence: int
    recommendation: str
    risk_level: str
    factors: list[str]

    model_config = {"from_attributes": True}


class ConfidenceScoreRecord(BaseModel):
    id: int
    user_id: int
    task_type: str
    confidence: float
    factors: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    actual_outcome: str | None = None
    was_accurate: int | None = None
    source: str | None = None
    related_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfidenceScoreListResponse(BaseModel):
    items: list[ConfidenceScoreRecord]
    total: int
