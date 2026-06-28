"""Execution Workflows API — DAG-based workflow orchestration."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.schemas.execution.workflow import WorkflowCreate, WorkflowResponse
from backend.app.services.execution.engine import ExecutionEngine
from backend.app.services.execution.tool_registry import get_tool_registry
from backend.app.services.execution.workflow import WorkflowOrchestrator

router = APIRouter()


def _get_orchestrator(db: Session) -> WorkflowOrchestrator:
    registry = get_tool_registry()
    engine = ExecutionEngine(db, registry)
    return WorkflowOrchestrator(db, engine)


@router.post("/create", response_model=WorkflowResponse)
def create_workflow(
    body: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Create a workflow."""
    orchestrator = _get_orchestrator(db)
    try:
        return orchestrator.create_workflow(
            current_user.id, body.name, body.steps, body.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=list[WorkflowResponse])
def list_workflows(
    status: str | None = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """List workflows for the current user."""
    orchestrator = _get_orchestrator(db)
    return orchestrator.get_user_workflows(current_user.id, status=status, limit=limit)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get a workflow by ID."""
    orchestrator = _get_orchestrator(db)
    wf = orchestrator.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.post("/{workflow_id}/run", response_model=WorkflowResponse)
def run_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Run a workflow."""
    orchestrator = _get_orchestrator(db)
    wf = orchestrator.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return orchestrator.run_workflow(workflow_id)


@router.post("/{workflow_id}/cancel", response_model=WorkflowResponse)
def cancel_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Cancel a workflow."""
    orchestrator = _get_orchestrator(db)
    wf = orchestrator.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return orchestrator.cancel_workflow(workflow_id)


@router.post("/{workflow_id}/duplicate", response_model=WorkflowResponse)
def duplicate_workflow(
    workflow_id: int,
    new_name: str = Query(..., description="Name for the duplicate"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Duplicate a workflow."""
    orchestrator = _get_orchestrator(db)
    wf = orchestrator.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    try:
        return orchestrator.duplicate_workflow(workflow_id, new_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
