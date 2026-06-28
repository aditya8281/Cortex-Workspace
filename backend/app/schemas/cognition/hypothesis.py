"""Hypothesis schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HypothesisCreate(BaseModel):
    hypothesis: str = Field(..., description="Hypothesis statement")
    evidence_for: list[dict[str, Any]] | None = None
    evidence_against: list[dict[str, Any]] | None = None
    source: str | None = None


class HypothesisUpdate(BaseModel):
    hypothesis: str | None = None
    status: str | None = None
    confidence: float | None = None
    resolution_reason: str | None = None


class HypothesisResponse(BaseModel):
    id: int
    user_id: int
    hypothesis: str
    evidence_for: list[dict[str, Any]]
    evidence_against: list[dict[str, Any]]
    confidence: float
    confidence_history: list[dict[str, Any]]
    status: str
    source: str | None = None
    related_plan_id: int | None = None
    related_hypothesis_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_reason: str | None = None

    model_config = {"from_attributes": True}


class HypothesisListResponse(BaseModel):
    items: list[HypothesisResponse]
    total: int
