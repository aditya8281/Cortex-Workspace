"""ToolExecution schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolExecutionCreate(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: dict[str, Any] | None = None
    workflow_id: int | None = None


class ToolExecutionUpdate(BaseModel):
    status: str | None = None
    result: dict[str, Any] | None = None
    error_message: str | None = None
    error_type: str | None = None
    duration_ms: int | None = None
    verification_result: dict[str, Any] | None = None


class ToolExecutionResponse(BaseModel):
    id: int
    user_id: int
    tool_name: str
    parameters: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    error_type: str | None = None
    verification_result: dict[str, Any] | None = None
    retry_count: int
    parent_execution_id: int | None = None
    workflow_id: int | None = None

    model_config = {"from_attributes": True}


class ExecutionStatsResponse(BaseModel):
    total: int
    successful: int
    failed: int
    success_rate: float
    average_duration_ms: float
    tool_breakdown: dict[str, int]


class ToolExecutionListResponse(BaseModel):
    items: list[ToolExecutionResponse]
    total: int
