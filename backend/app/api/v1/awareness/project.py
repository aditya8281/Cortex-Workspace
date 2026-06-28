"""Project awareness API — project type and framework detection."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.services.awareness.project_scanner import ProjectScannerService

router = APIRouter(prefix="/project", tags=["awareness-project"])


@router.get("/scan", response_model=dict[str, Any])
def scan_project(
    project_path: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan a project and detect its type, frameworks, and features."""
    service = ProjectScannerService(db)
    project = service.scan_project(current_user.id, project_path)
    return {
        "id": project.id,
        "project_path": project.project_path,
        "project_name": project.project_name,
        "project_type": project.project_type,
        "frameworks": json.loads(project.frameworks) if project.frameworks else [],
        "configuration": json.loads(project.configuration) if project.configuration else {},
        "has_tests": project.has_tests,
        "has_ci": project.has_ci,
        "has_docker": project.has_docker,
        "last_scanned": project.last_scanned.isoformat() if project.last_scanned else None,
    }
