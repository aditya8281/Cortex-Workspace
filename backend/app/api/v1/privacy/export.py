"""Privacy Data Export API — GDPR Article 20 data portability endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.privacy.export import ExportCreate, ExportResponse
from backend.app.services.privacy.export import DataExportService

router = APIRouter()


@router.post("/create", response_model=ExportResponse)
def create_export(
    body: ExportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a data export request (async processing)."""
    service = DataExportService(db)
    export = service.create_export(
        user_id=current_user.id,
        export_type=body.export_type,
        data_types=body.data_types,
        format=body.format,
    )
    return export


@router.post("/{export_id}/process", response_model=ExportResponse)
def process_export(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process a pending data export (gather, serialize, store)."""
    service = DataExportService(db)
    export = service.process_export(export_id)
    if export.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


@router.get("/{export_id}/verify", response_model=dict[str, Any])
def verify_export(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify export integrity via SHA-256 checksum."""
    service = DataExportService(db)
    return service.verify_export(export_id)
