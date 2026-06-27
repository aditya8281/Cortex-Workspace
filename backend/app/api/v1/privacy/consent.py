"""Privacy Consent Management API — consent grant, revoke, check."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.privacy.consent import ConsentResponse
from backend.app.services.privacy.access_control import AccessControlService

router = APIRouter()


class ConsentGrantRequest(BaseModel):
    """Request body for granting consent."""

    consent_type: str = Field(..., description="Consent type identifier")
    scope: str | None = Field(None, description="Scope of consent")
    context: dict[str, Any] | None = Field(None, description="Additional context")


@router.get("/", response_model=list[ConsentResponse])
def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all consent records for the current user."""
    from sqlalchemy import select

    from backend.app.models.privacy.consent import ConsentRecord

    stmt = (
        select(ConsentRecord).where(ConsentRecord.user_id == current_user.id).order_by(ConsentRecord.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


@router.get("/check", response_model=dict)
def check_consent(
    consent_type: str = Query(..., description="Consent type to check"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if active consent exists for a given type."""
    service = AccessControlService(db)
    granted = service.check_consent(current_user.id, consent_type)
    return {"consent_type": consent_type, "granted": granted}


@router.post("/grant", response_model=ConsentResponse)
def grant_consent(
    body: ConsentGrantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grant or upgrade consent for the current user."""
    service = AccessControlService(db)
    return service.grant_consent(
        user_id=current_user.id,
        consent_type=body.consent_type,
        scope=body.scope,
        context=body.context,
    )


@router.post("/revoke", response_model=dict)
def revoke_consent(
    consent_type: str = Query(..., description="Consent type to revoke"),
    reason: str | None = Query(None, description="Revocation reason"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke consent for a given type."""
    service = AccessControlService(db)
    success = service.revoke_consent(current_user.id, consent_type, reason=reason)
    return {"consent_type": consent_type, "success": success}
