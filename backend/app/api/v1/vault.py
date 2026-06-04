import os
import shutil
import logging
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_optional, get_db
from backend.app.models.user import User
from backend.app.services.memory_manager import memory_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ChangePathPayload(BaseModel):
    path: str


def get_dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += get_dir_size(Path(entry.path))
    return total


@router.get("/settings")
def get_vault_settings(current_user: User | None = Depends(get_current_user_optional)):
    """
    Retrieve current memory vault path, status, and category size stats.
    """
    try:
        active_path = memory_manager.get_memory_path()
        categories_stats = {}
        total_size = 0

        for cat in memory_manager.CATEGORIES:
            cat_path = active_path / cat
            if cat_path.exists():
                size = get_dir_size(cat_path)
                file_count = len([f for f in cat_path.iterdir() if f.is_file()])
                categories_stats[cat] = {
                    "size_bytes": size,
                    "file_count": file_count
                }
                total_size += size
            else:
                categories_stats[cat] = {
                    "size_bytes": 0,
                    "file_count": 0
                }

        return {
            "active_path": str(active_path),
            "is_paused": memory_manager.is_indexing_paused(),
            "total_size_bytes": total_size,
            "categories": categories_stats
        }
    except Exception as e:
        logger.exception("Failed to fetch vault settings")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/change-path")
def change_vault_path(payload: ChangePathPayload, current_user: User | None = Depends(get_current_user_optional)):
    """
    Migrate memory vault files to a new directory path.
    """
    target_path = Path(payload.path).expanduser().resolve()
    try:
        memory_manager.validate_memory_path(target_path)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    try:
        memory_manager.change_memory_vault(str(target_path))
        return {
            "status": "success",
            "message": f"Memory vault migrated successfully to {target_path}",
            "active_path": str(target_path)
        }
    except Exception as e:
        logger.exception("Failed to migrate memory vault to %s", target_path)
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/reset")
def reset_vault(current_user: User | None = Depends(get_current_user_optional)):
    """
    Perform a complete one-folder reset of the memory vault.
    """
    try:
        memory_manager.reset_vault()
        return {
            "status": "success",
            "message": "Memory vault successfully reset to an empty state."
        }
    except Exception as e:
        logger.exception("Failed to reset memory vault")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/export")
def export_vault(current_user: User | None = Depends(get_current_user_optional)):
    """
    Zips the entire cortex brain vault and returns it as a file response.
    """
    try:
        # Create temporary zip target under vault temp directory
        temp_dir = memory_manager.get_path("temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_file_path = temp_dir / "cortex_brain_vault_backup.zip"
        
        # Export
        memory_manager.export_memory(str(zip_file_path))
        
        if not zip_file_path.exists():
            raise FileNotFoundError("Backup file creation failed.")

        return FileResponse(
            path=str(zip_file_path),
            filename="cortex_brain_vault_backup.zip",
            media_type="application/zip"
        )
    except Exception as e:
        logger.exception("Failed to export memory vault zip")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_vault(file: UploadFile = File(...), current_user: User | None = Depends(get_current_user_optional)):
    """
    Upload and restore a memory vault from a backup zip file.
    """
    try:
        temp_dir = memory_manager.get_path("temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_file_path = temp_dir / "uploaded_backup.zip"

        with open(zip_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Restore from backup
        memory_manager.import_memory(str(zip_file_path))
        
        # Delete uploaded temp zip
        if zip_file_path.exists():
            zip_file_path.unlink()

        return {
            "status": "success",
            "message": "Memory vault successfully restored from backup zip."
        }
    except Exception as e:
        logger.exception("Failed to import memory vault zip")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
