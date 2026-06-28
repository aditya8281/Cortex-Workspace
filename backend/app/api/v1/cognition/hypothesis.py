"""Cognition Hypothesis API — hypothesis generation and evidence tracking."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.schemas.cognition.hypothesis import (
    HypothesisCreate,
    HypothesisResponse,
)
from backend.app.services.cognition.hypothesis import HypothesisService

router = APIRouter()


@router.post("/generate", response_model=HypothesisResponse)
def generate_hypothesis(
    body: HypothesisCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Generate a new hypothesis."""
    service = HypothesisService(db)
    return service.generate_hypothesis(
        user_id=current_user.id,
        hypothesis=body.hypothesis,
        evidence_for=body.evidence_for,
        evidence_against=body.evidence_against,
        source=body.source,
    )


@router.get("/active", response_model=list[HypothesisResponse])
def list_active(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """List all active hypotheses."""
    service = HypothesisService(db)
    return service.get_active_hypotheses(current_user.id)


@router.get("/high-confidence", response_model=list[HypothesisResponse])
def list_high_confidence(
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """List high-confidence active hypotheses."""
    service = HypothesisService(db)
    return service.get_high_confidence_hypotheses(current_user.id, threshold)


@router.get("/{hypothesis_id}", response_model=HypothesisResponse)
def get_hypothesis(
    hypothesis_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Get a hypothesis by ID."""
    service = HypothesisService(db)
    hypo = service.get_hypothesis(hypothesis_id)
    if not hypo or hypo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypo


@router.post("/{hypothesis_id}/evidence", response_model=HypothesisResponse)
def add_evidence(
    hypothesis_id: int,
    evidence: str = Query(..., description="Evidence text"),
    supports: bool = Query(True, description="True=supports, False=contradicts"),
    weight: float = Query(1.0, ge=0.0, le=1.0, description="Evidence reliability"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Add evidence to a hypothesis."""
    service = HypothesisService(db)
    hypo = service.get_hypothesis(hypothesis_id)
    if not hypo or hypo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return service.add_evidence(hypothesis_id, evidence, supports, weight)


@router.post("/{hypothesis_id}/resolve", response_model=HypothesisResponse)
def resolve_hypothesis(
    hypothesis_id: int,
    status: str = Query(..., description="confirmed or rejected"),
    reason: str | None = Query(None, description="Resolution reason"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Resolve a hypothesis."""
    service = HypothesisService(db)
    hypo = service.get_hypothesis(hypothesis_id)
    if not hypo or hypo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    try:
        return service.resolve_hypothesis(hypothesis_id, status, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/merge", response_model=HypothesisResponse)
def merge_hypotheses(
    hypothesis_id: int = Query(..., description="Primary hypothesis ID"),
    other_id: int = Query(..., description="Hypothesis to merge"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Merge two hypotheses."""
    service = HypothesisService(db)
    hypo = service.get_hypothesis(hypothesis_id)
    if not hypo or hypo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    try:
        return service.merge_hypotheses(hypothesis_id, other_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
