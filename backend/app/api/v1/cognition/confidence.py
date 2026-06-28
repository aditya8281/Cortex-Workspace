"""Cognition Confidence API — confidence estimation and calibration."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.schemas.cognition.confidence import ConfidenceEstimate, ConfidenceResponse
from backend.app.services.cognition.confidence import ConfidenceEstimationService

router = APIRouter()


@router.post("/estimate", response_model=ConfidenceResponse)
def estimate_confidence(
    body: ConfidenceEstimate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Estimate confidence for a task type."""
    ctx = body.context or {}
    ctx["user_id"] = current_user.id
    service = ConfidenceEstimationService(db)
    return service.estimate_task_confidence(body.task_type, context=ctx)


@router.post("/combine")
def combine_confidences(
    confidences: list[int] = Query(..., description="Confidence scores to combine"),
    weights: list[float] | None = Query(None, description="Weights for each score"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Combine multiple confidence scores."""
    service = ConfidenceEstimationService(db)
    return service.combine_confidences(confidences, weights)


@router.get("/calibration")
def get_calibration(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Get calibration data for confidence predictions."""
    service = ConfidenceEstimationService(db)
    return service.get_calibration_data(current_user.id, days=days)
