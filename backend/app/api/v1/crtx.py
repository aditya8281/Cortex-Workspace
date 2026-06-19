"""CRTX Export/Import API — Portable encrypted Cortex user archives.

⚠️  EXPERIMENTAL — NOT PART OF CURRENT RELEASE
This module is retained for future .crtx portability work.
Routes are disconnected from the active API router (see backend/app/api/router.py).
Do not extend or build new features on top of this module.

Exports and imports complete user packages as encrypted .crtx files.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.auth.dependencies import require_admin
from backend.app.models.user import User

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────


class CrtxExportRequest(BaseModel):
    export_password: str
    confirm_password: str


class CrtxImportResponse(BaseModel):
    user_id: int
    username: str
    vault_files_restored: int
    message: str


# ── Endpoints ────────────────────────────────────────────────────────


@router.post("/export")
def export_crtx(
    body: CrtxExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export the current user as an encrypted .crtx archive.

    The archive contains: profile, avatar, settings, preferences,
    chat history, vault contents, and all personal metadata.

    Explicitly excluded: CortexMemory, embeddings, indexes, repositories,
    vector stores, AI cache, execution logs, downloaded models.
    """
    if body.export_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if len(body.export_password) < 8:
        raise HTTPException(status_code=400, detail="Export password must be at least 8 characters")

    from fastapi.responses import Response

    from backend.app.services.crtx_service import export_crtx

    archive_name = f"cortex_export_{current_user.username}_{current_user.id}.crtx"
    tmp_fd, archive_path = tempfile.mkstemp(suffix=".crtx")
    os.close(tmp_fd)

    try:
        export_crtx(db, current_user.id, body.export_password, archive_path)
        file_bytes = Path(archive_path).read_bytes()
        return Response(
            content=file_bytes,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{archive_name}"'},
        )
    finally:
        try:
            os.unlink(archive_path)
        except OSError:
            pass


@router.post("/verify")
async def verify_crtx(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
):
    """Verify a .crtx archive without decrypting.

    Returns metadata and manifest info for verification.
    """
    if not file.filename or not file.filename.endswith(".crtx"):
        raise HTTPException(status_code=400, detail="File must have .crtx extension")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".crtx", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from backend.app.services.crtx_service import verify_crtx
        return verify_crtx(tmp_path)
    finally:
        os.unlink(tmp_path)


@router.post("/import", response_model=CrtxImportResponse)
async def import_crtx(
    file: UploadFile = File(...),
    export_password: str = Form(...),
    new_storage_root: str = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Import a .crtx archive.

    Restores the complete user profile, vault contents, and settings.
    Requires a new local storage location for the imported user.
    """
    if not file.filename or not file.filename.endswith(".crtx"):
        raise HTTPException(status_code=400, detail="File must have .crtx extension")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".crtx", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from backend.app.services.crtx_service import import_crtx
        result = import_crtx(db, tmp_path, export_password, new_storage_root)
        return CrtxImportResponse(
            user_id=result["user_id"],
            username=result["username"],
            vault_files_restored=result["vault_files_restored"],
            message="User imported successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")
    finally:
        os.unlink(tmp_path)
