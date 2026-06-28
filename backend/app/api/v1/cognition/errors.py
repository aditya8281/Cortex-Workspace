"""Cognition Error Analysis API — error analysis and pattern detection."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.schemas.cognition.error_analysis import (
    ErrorAnalysisCreate,
    ErrorAnalysisResponse,
)
from backend.app.services.cognition.error_analysis import ErrorAnalysisService

router = APIRouter()


@router.post("/analyze", response_model=ErrorAnalysisResponse)
def analyze_error(
    body: ErrorAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Analyze an error and determine root cause."""
    service = ErrorAnalysisService(db)
    return service.analyze_error(
        current_user.id,
        body.error_type,
        body.error_message or "",
        body.context,
    )


@router.get("/patterns")
def get_error_patterns(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get common error patterns for the current user."""
    service = ErrorAnalysisService(db)
    return service.get_error_patterns(current_user.id, days=days)


@router.get("/analyses", response_model=list[ErrorAnalysisResponse])
def list_analyses(
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """List error analyses for the current user."""
    service = ErrorAnalysisService(db)
    return service.get_user_analyses(
        current_user.id, severity=severity, limit=limit
    )


@router.get("/analysis/{analysis_id}", response_model=ErrorAnalysisResponse)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get a specific error analysis."""
    service = ErrorAnalysisService(db)
    analysis = service.get_analysis(analysis_id)
    if not analysis or analysis.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.post("/analysis/{analysis_id}/resolve", response_model=ErrorAnalysisResponse)
def resolve_error(
    analysis_id: int,
    resolution_method: str = Query("manual", description="Resolution method"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Mark an error as resolved."""
    service = ErrorAnalysisService(db)
    analysis = service.get_analysis(analysis_id)
    if not analysis or analysis.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return service.resolve_error(analysis_id, resolution_method)
