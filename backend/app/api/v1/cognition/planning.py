"""Cognition Planning API — task planning and decomposition."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.schemas.cognition.task_plan import (
    TaskPlanCreate,
    TaskPlanListResponse,
    TaskPlanResponse,
)
from backend.app.services.cognition.planning import TaskPlanningService

router = APIRouter()


@router.post("/plan", response_model=TaskPlanResponse)
def create_plan(
    body: TaskPlanCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Create a task plan by decomposing a goal into steps."""
    service = TaskPlanningService(db)
    plan = service.create_plan(
        user_id=current_user.id,
        goal=body.goal,
        steps=body.steps,
    )
    return plan


@router.get("/plan/{plan_id}", response_model=TaskPlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get a task plan by ID."""
    service = TaskPlanningService(db)
    plan = service.get_plan(plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/plans", response_model=TaskPlanListResponse)
def list_plans(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """List task plans for the current user."""
    service = TaskPlanningService(db)
    plans = service.get_user_plans(
        current_user.id, status=status, limit=limit, offset=offset
    )
    return TaskPlanListResponse(
        items=[TaskPlanResponse.model_validate(p) for p in plans],
        total=len(plans),
        page=(offset // limit) + 1,
        page_size=limit,
    )


@router.post("/plan/{plan_id}/step/{step_index}", response_model=TaskPlanResponse)
def execute_step(
    plan_id: int,
    step_index: int,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Execute a specific step in a plan."""
    service = TaskPlanningService(db)
    plan = service.get_plan(plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        return service.execute_step(plan_id, step_index, result=result, error=error)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan/{plan_id}/step/{step_index}/skip", response_model=TaskPlanResponse)
def skip_step(
    plan_id: int,
    step_index: int,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Skip a step in a plan."""
    service = TaskPlanningService(db)
    plan = service.get_plan(plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        return service.skip_step(plan_id, step_index, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan/{plan_id}/cancel", response_model=TaskPlanResponse)
def cancel_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Cancel a task plan."""
    service = TaskPlanningService(db)
    plan = service.get_plan(plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return service.cancel_plan(plan_id)


@router.get("/plan/{plan_id}/next-steps")
def get_next_steps(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Get indices of steps ready to execute (dependencies satisfied)."""
    service = TaskPlanningService(db)
    plan = service.get_plan(plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
    steps = service.get_next_executable_steps(plan_id)
    return {"plan_id": plan_id, "ready_steps": steps}
