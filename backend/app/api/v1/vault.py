"""Vault API — Encrypted personal document locker endpoints.

The vault is NOT part of Cortex Memory. It never participates in RAG,
embeddings, indexing, or AI processing.

Two-password architecture:
  1. Login Password  — account authentication
  2. Vault Password  — private vault access
"""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.vault import (
    VaultChangePasswordResponse,
    VaultDeleteResponse,
    VaultExportResponse,
    VaultFileInfo,
    VaultFolderResponse,
    VaultLockResponse,
    VaultMetadataResponse,
    VaultMoveResponse,
    VaultRenameResponse,
    VaultSearchResponse,
    VaultStatusResponse,
    VaultUploadResponse,
)
from backend.app.services import vault_service

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────


class VaultUnlockRequest(BaseModel):
    vault_password: str


class VaultUnlockResponse(BaseModel):
    unlocked: bool
    message: str


class VaultRenameRequest(BaseModel):
    new_name: str


class VaultFolderRequest(BaseModel):
    folder_path: str


class VaultSearchRequest(BaseModel):
    query: str


class VaultMetadataUpdateRequest(BaseModel):
    favorite: bool | None = None
    tags: list[str] | None = None


class VaultMoveRequest(BaseModel):
    source_path: str
    destination_folder: str


class VaultExportRequest(BaseModel):
    paths: list[str]
    destination_dir: str


class VaultChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ── Lock / Unlock ────────────────────────────────────────────────────


@router.post("/unlock", response_model=VaultUnlockResponse)
async def unlock_vault(
    body: VaultUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unlock the vault with the vault password."""
    import time

    from backend.app.core.redis import redis_cache

    # Rate-limit vault attempts: max 5 per minute per user
    rate_key = f"vault_unlock:{current_user.id}"
    try:
        raw = await redis_cache.get(rate_key)
        attempts = raw if isinstance(raw, dict) and "count" in raw else {"count": 0, "window_start": time.time()}
        if time.time() - attempts["window_start"] > 60:
            attempts = {"count": 0, "window_start": time.time()}
        attempts["count"] += 1
        await redis_cache.set(rate_key, attempts, expire_seconds=60)
        if attempts["count"] > 5:
            raise HTTPException(status_code=429, detail="Too many vault unlock attempts. Try again later.")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Vault rate limiter Redis failure, falling back to in-memory: %s", e)
        # In-memory fallback when Redis is down
        import time as _time
        now = _time.time()
        if not hasattr(unlock_vault, '_attempts'):
            unlock_vault._attempts = {}
        user_key = str(current_user.id)
        attempts = unlock_vault._attempts.get(user_key, {"count": 0, "window_start": now})
        if now - attempts["window_start"] > 60:
            attempts = {"count": 0, "window_start": now}
        attempts["count"] += 1
        unlock_vault._attempts[user_key] = attempts
        if attempts["count"] > 5:
            raise HTTPException(status_code=429, detail="Too many vault unlock attempts. Try again later.")

    success = vault_service.unlock_vault(db, current_user, body.vault_password)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid vault password")

    # Clear rate limit on successful unlock
    try:
        await redis_cache.delete(rate_key)
    except Exception:
        pass

    return VaultUnlockResponse(unlocked=True, message="Vault unlocked")


@router.post("/lock", response_model=VaultLockResponse)
def lock_vault(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lock the vault."""
    vault_service.lock_vault(db, current_user)
    return {"locked": True, "message": "Vault locked"}


@router.get("/status", response_model=VaultStatusResponse)
def vault_status(
    current_user: User = Depends(get_current_user),
):
    """Check vault lock status."""
    from backend.app.services.vault_service import is_vault_unlocked

    return {
        "locked": not is_vault_unlocked(current_user),
        "has_vault_password": current_user.vault_password_hash is not None,
    }


# ── File Operations ──────────────────────────────────────────────────


@router.get("/files", response_model=list[VaultFileInfo])
def list_files(
    folder: str = "/",
    recursive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List files in the vault. Requires unlocked vault."""
    vault_service._require_unlocked(current_user)
    files = vault_service.list_vault_files(db, current_user.id, folder, recursive)
    return files


@router.post("/files/upload", response_model=VaultUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = "/",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a file to a specific folder in the vault."""
    vault_service._require_unlocked(current_user)
    content = await file.read()
    filename = file.filename or "unnamed"

    clean_folder = folder.strip("/")
    file_path = f"{clean_folder}/{filename}" if clean_folder else filename

    return vault_service.upload_vault_file(db, current_user.id, file_path, content)


def get_mime_type(filename: str) -> str:
    from pathlib import Path

    ext = Path(filename).suffix.lower()
    mapping = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".json": "application/json",
        ".csv": "text/csv",
    }
    return mapping.get(ext, "application/octet-stream")


@router.get("/files/preview/{file_path:path}")
def preview_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Preview a decrypted file from the vault inline."""
    vault_service._require_unlocked(current_user)
    content = vault_service.download_vault_file(db, current_user.id, file_path)
    filename = file_path.split("/")[-1]
    safe_name = filename.replace('"', '_')
    mime_type = get_mime_type(filename)
    return StreamingResponse(
        io.BytesIO(content),
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.get("/files/download/{file_path:path}")
def download_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download and decrypt a file from the vault. Decrypts automatically using the cached vault key."""
    vault_service._require_unlocked(current_user)
    content = vault_service.download_vault_file(db, current_user.id, file_path)
    filename = file_path.split("/")[-1]
    safe_name = filename.replace('"', '_')
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.delete("/files/{file_path:path}", response_model=VaultDeleteResponse)
def delete_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a file or folder from the vault."""
    vault_service._require_unlocked(current_user)
    success = vault_service.delete_vault_file(db, current_user.id, file_path)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"deleted": True}


@router.put("/files/{file_path:path}/rename", response_model=VaultRenameResponse)
def rename_file(
    file_path: str,
    body: VaultRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename a file or folder in the vault."""
    vault_service._require_unlocked(current_user)
    return vault_service.rename_vault_item(db, current_user.id, file_path, body.new_name)


@router.post("/files/move", response_model=VaultMoveResponse)
def move_file(
    body: VaultMoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move a file or folder to a new destination folder in the vault."""
    vault_service._require_unlocked(current_user)
    return vault_service.move_vault_item(db, current_user.id, body.source_path, body.destination_folder)


@router.put("/files/{file_path:path}/metadata", response_model=VaultMetadataResponse)
def update_file_metadata(
    file_path: str,
    body: VaultMetadataUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update favorite status or tags for a file/folder in the vault."""
    vault_service._require_unlocked(current_user)
    return vault_service.update_vault_metadata(db, current_user.id, file_path, body.favorite, body.tags)


@router.post("/folders", response_model=VaultFolderResponse)
def create_folder(
    body: VaultFolderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a folder in the vault."""
    vault_service._require_unlocked(current_user)
    return vault_service.create_vault_folder(db, current_user.id, body.folder_path)


@router.post("/search", response_model=VaultSearchResponse)
def search_files(
    body: VaultSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search vault files by name."""
    vault_service._require_unlocked(current_user)
    return vault_service.search_vault_files(db, current_user.id, body.query)


@router.post("/files/export", response_model=VaultExportResponse)
def export_files(
    body: VaultExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export decrypted vault files/folders recursively to a local directory."""
    vault_service._require_unlocked(current_user)
    return vault_service.export_vault_items(db, current_user.id, body.paths, body.destination_dir)


@router.post("/change-password", response_model=VaultChangePasswordResponse)
def change_password(
    body: VaultChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rotate the vault password and re-encrypt files."""
    vault_service._require_unlocked(current_user)
    success = vault_service.change_vault_password(db, current_user, body.old_password, body.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to rotate password. Check old password.")
    return {"message": "Vault password changed and files re-encrypted successfully"}
