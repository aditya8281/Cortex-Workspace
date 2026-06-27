"""Privacy Transparency API — explainable AI decisions endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.services.privacy.transparency import TransparencyService

router = APIRouter()


class ExplainRequest(BaseModel):
    """Request body for generating a decision explanation."""

    decision_type: str = Field(
        ...,
        description="Decision type: memory_retrieval, hypothesis_scoring, tool_selection, error_analysis, access_decision",
    )
    context: dict = Field(default_factory=dict, description="Context data for the explanation")


@router.post("/explain", response_model=dict)
def explain_decision(
    body: ExplainRequest,
    current_user: User = Depends(get_current_user),  # noqa: ARG001
    db: Session = Depends(get_db),  # noqa: ARG001
):
    """Generate a structured explanation for an automated decision."""
    service = TransparencyService()
    return service.explain_decision(body.decision_type, body.context)


@router.get("/templates")
def get_decision_templates(
    current_user: User = Depends(get_current_user),  # noqa: ARG001
    db: Session = Depends(get_db),  # noqa: ARG001
):
    """Get available decision templates and their factor definitions."""
    service = TransparencyService()
    return service.DECISION_TEMPLATES
