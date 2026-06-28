"""Execution Tools API — tool execution, registry, and statistics."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.schemas.execution.tool_execution import (
    ExecutionStatsResponse,
    ToolExecutionCreate,
    ToolExecutionResponse,
)
from backend.app.services.execution.engine import ExecutionEngine
from backend.app.services.execution.tool_registry import get_tool_registry

router = APIRouter()


@router.post("/execute", response_model=ToolExecutionResponse)
def execute_tool(
    body: ToolExecutionCreate,
    auto_verify: bool = Query(True, description="Run safety verification"),
    confirmed: bool = Query(False, description="Confirm dangerous operations"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Execute a registered tool."""
    registry = get_tool_registry()
    engine = ExecutionEngine(db, registry)

    if not registry.has_tool(body.tool_name):
        raise HTTPException(status_code=404, detail=f"Tool '{body.tool_name}' not found")

    return engine.execute_tool(
        user_id=current_user.id,
        tool_name=body.tool_name,
        params=body.parameters or {},
        auto_verify=auto_verify,
        confirmed=confirmed,
    )


@router.post("/execute-with-retry", response_model=ToolExecutionResponse)
def execute_with_retry(
    body: ToolExecutionCreate,
    max_retries: int = Query(3, ge=0, le=10),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Execute a tool with automatic retry on failure."""
    registry = get_tool_registry()
    engine = ExecutionEngine(db, registry)

    if not registry.has_tool(body.tool_name):
        raise HTTPException(status_code=404, detail=f"Tool '{body.tool_name}' not found")

    return engine.execute_with_retry(
        user_id=current_user.id,
        tool_name=body.tool_name,
        params=body.parameters or {},
        max_retries=max_retries,
    )


@router.get("/list")
def list_tools(
    category: str | None = Query(None, description="Filter by category"),
) -> list[dict[str, Any]]:
    """List all registered tools."""
    registry = get_tool_registry()
    return registry.list_tools(category=category)


@router.get("/stats", response_model=ExecutionStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get execution statistics for the current user."""
    registry = get_tool_registry()
    engine = ExecutionEngine(db, registry)
    return engine.get_execution_stats(current_user.id)


@router.get("/{execution_id}", response_model=ToolExecutionResponse)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get an execution by ID."""
    registry = get_tool_registry()
    engine = ExecutionEngine(db, registry)
    execution = engine.get_execution(execution_id)
    if not execution or execution.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
