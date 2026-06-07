from __future__ import annotations

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.app.api.deps import get_current_user, get_current_user_optional, get_db
from backend.app.models.user import User
from backend.app.services.storage_registry import get_registry_for_user, register_user_storage
from backend.app.core.storage_abstraction import get_user_storage, validate_storage_path
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


class ChangePathPayload(BaseModel):
    path: str


def get_dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total


@router.get("/settings")
def get_vault_settings(current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        storage = get_user_storage(current_user.id)
        categories_stats = {}
        total_size = 0
        for cat in ["documents", "images", "certificates", "notes", "others", "metadata", "temp"]:
            cat_path = storage.vault / cat
            size = get_dir_size(cat_path)
            file_count = len([f for f in cat_path.iterdir() if f.is_file()]) if cat_path.exists() else 0
            categories_stats[cat] = {"size_bytes": size, "file_count": file_count}
            total_size += size

        return {
            "active_path": str(storage.vault),
            "total_size_bytes": total_size,
            "categories": categories_stats,
        }
    except Exception as e:
        logger.exception("Failed to fetch vault settings")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/change-path")
def change_vault_path(
    payload: ChangePathPayload,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    target_path = validate_storage_path(payload.path)
    current_storage = get_user_storage(current_user.id)
    if current_storage.root == target_path:
        return {
            "status": "success",
            "message": "Storage path already set to requested location.",
            "active_path": str(current_storage.root),
        }

    try:
        target_path.mkdir(parents=True, exist_ok=True)
        if any(target_path.iterdir()):
            raise HTTPException(status_code=400, detail="Target storage root must be empty")

        shutil.move(str(current_storage.root), str(target_path))
        entry = register_user_storage(db, current_user.id, str(target_path))
        return {
            "status": "success",
            "message": f"Storage root migrated successfully to {target_path}",
            "active_path": entry.storage_root,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to migrate user storage to %s", target_path)
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/reset")
def reset_vault(current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        storage = get_user_storage(current_user.id)
        if storage.vault.exists():
            shutil.rmtree(storage.vault)
        storage.vault.mkdir(parents=True, exist_ok=True)
        for cat in ["documents", "images", "certificates", "notes", "others", "metadata", "temp"]:
            (storage.vault / cat).mkdir(parents=True, exist_ok=True)
        return {"status": "success", "message": "User vault reset to empty state."}
    except Exception as e:
        logger.exception("Failed to reset user vault")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/export")
def export_vault(current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        storage = get_user_storage(current_user.id)
        temp_dir = storage.exports / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_file_path = temp_dir / "user_vault_backup.zip"
        from backend.app.services.vault_manager import vault_manager
        vault_manager.export_vault(current_user.id, str(zip_file_path))
        if not zip_file_path.exists():
            raise FileNotFoundError("Backup file creation failed.")
        return FileResponse(path=str(zip_file_path), filename="user_vault_backup.zip", media_type="application/zip")
    except Exception as e:
        logger.exception("Failed to export memory vault zip")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_vault(file: UploadFile = File(...), current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        storage = get_user_storage(current_user.id)
        temp_dir = storage.exports / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_file_path = temp_dir / "uploaded_backup.zip"

        with open(zip_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        from backend.app.services.vault_manager import vault_manager
        vault_manager.import_vault(current_user.id, str(zip_file_path))

        if zip_file_path.exists():
            zip_file_path.unlink()

        return {
            "status": "success",
            "message": "Memory vault successfully restored from backup zip."
        }
    except Exception as e:
        logger.exception("Failed to import memory vault zip")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

