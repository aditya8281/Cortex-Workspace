"""TaskPlan schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskStep(BaseModel):
    step: int = Field(..., description="Step index (0-based)")
    description: str = Field(..., description="What this step does")
    status: str = Field("pending")
    depends_on: list[int] | None = None
    tool: str | None = None
    params: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class TaskPlanCreate(BaseModel):
    goal: str = Field(..., description="High-level goal to decompose")
    steps: list[dict[str, Any]] | None = None


class TaskPlanUpdate(BaseModel):
    goal: str | None = None
    steps: list[dict[str, Any]] | None = None
    status: str | None = None
    current_step: int | None = None
    confidence: float | None = None


class TaskPlanResponse(BaseModel):
    id: int
    user_id: int
    goal: str
    steps: list[dict[str, Any]]
    current_step: int
    status: str
    confidence: float | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    estimated_duration_ms: int | None = None
    actual_duration_ms: int | None = None

    model_config = {"from_attributes": True}


class TaskPlanListResponse(BaseModel):
    items: list[TaskPlanResponse]
    total: int
    page: int
    page_size: int
