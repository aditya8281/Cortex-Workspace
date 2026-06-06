import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

from backend.app.services.memory_manager import memory_manager
from backend.app.core.rbac import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/change-path")
def change_brain_vault_path(payload: dict, admin_user=Depends(require_admin)):
    target = payload.get("path")
    if not target:
        raise HTTPException(status_code=400, detail="Missing 'path' in payload")
    try:
        # Disabled: memory relocation removed from Cortex architecture
        raise HTTPException(status_code=405, detail="Memory relocation is disabled. System memory is fixed under cortex_system/memory")
    except Exception as e:
        logger.exception("Brain vault migration failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
def reset_brain_vault(admin_user=Depends(require_admin)):
    try:
        memory_manager.reset_vault()
        return {"status": "success", "message": "Brain vault reset"}
    except Exception as e:
        logger.exception("Brain vault reset failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
def export_brain_vault(admin_user=Depends(require_admin)):
    try:
        temp = memory_manager.get_path("temp")
        temp.mkdir(parents=True, exist_ok=True)
        zip_path = temp / "brain_vault_backup.zip"
        memory_manager.export_memory(str(zip_path))
        return {"status": "success", "path": str(zip_path)}
    except Exception as e:
        logger.exception("Brain vault export failed")
        raise HTTPException(status_code=500, detail=str(e))
