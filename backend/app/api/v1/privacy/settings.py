"""Model settings, storage, and sync endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.db import get_current_user, get_db
from backend.app.models.intelligence.model_catalog import ModelCatalog
from backend.app.models.interaction.user import User
from backend.app.models.privacy.user_settings import UserModelSettings
from backend.app.schemas.intelligence.model import (
    CatalogueRefreshResponse,
    ModelSettingsResponse,
    ModelSettingsUpdate,
    ModelUpdate,
    ModelUpdatesResponse,
    StorageUsageResponse,
    SyncTriggerResponse,
    UsageStatsResponse,
)
from backend.app.services.sync.service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models/usage/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get model usage statistics."""
    from backend.app.services.system.usage import UsageTracker

    tracker = UsageTracker(db)
    return tracker.get_usage_stats()


@router.post("/models/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    provider: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger a sync from providers."""
    try:
        service = SyncService(db)
        job = await service.sync_library(provider_name=provider)
        return {
            "job_id": str(job.id),
            "status": job.status,
            "models_discovered": job.models_discovered,
            "models_added": job.models_added,
            "models_updated": job.models_updated,
            "error_message": job.error_message,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Provider error")
    except Exception as e:
        logger.error("sync_failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models/storage", response_model=StorageUsageResponse)
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
):
    """Get storage usage breakdown."""
    models_dir = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "models"

    try:
        disk = psutil.disk_usage(".")
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
    except Exception as e:
        logger.warning("Failed to get disk usage: %s", e)
        total_gb = used_gb = free_gb = 0

    models_size = 0
    if models_dir.exists():
        for f in models_dir.rglob("*"):
            if f.is_file():
                models_size += f.stat().st_size

    return {
        "total_disk_gb": round(total_gb, 1),
        "used_disk_gb": round(used_gb, 1),
        "free_disk_gb": round(free_gb, 1),
        "models_total_gb": round(models_size / (1024**3), 1),
        "models": [],
        "cache_gb": 0.0,
    }


@router.get("/models/updates", response_model=ModelUpdatesResponse)
async def check_model_updates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check for available model updates."""
    updates: list[ModelUpdate] = []

    try:
        import httpx

        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5.0) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            installed = resp.json().get("models", [])
    except Exception as e:
        logger.warning("Failed to check for model updates: %s", e)
        return {"updates": []}

    for model in installed:
        tag = model.get("name", "")
        base_name = tag.split(":")[0] if ":" in tag else tag
        installed_version = tag.split(":")[1] if ":" in tag else "latest"

        catalog_entry = db.execute(select(ModelCatalog).where(ModelCatalog.model_id == base_name)).scalar_one_or_none()

        if not catalog_entry:
            updates.append(
                ModelUpdate(
                    model_id=base_name,
                    display_name=base_name.replace("-", " ").title(),
                    installed_version=installed_version,
                    available_version=None,
                    update_type="new",
                )
            )
            continue

        catalog_version = catalog_entry.version
        if catalog_version and installed_version != catalog_version and installed_version != "latest":
            updates.append(
                ModelUpdate(
                    model_id=base_name,
                    display_name=catalog_entry.display_name,
                    installed_version=installed_version,
                    available_version=catalog_version,
                    update_type="version",
                )
            )

    return {"updates": updates}


@router.get("/models/settings", response_model=ModelSettingsResponse)
async def get_model_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user model settings."""
    settings_row = db.execute(
        select(UserModelSettings).where(UserModelSettings.user_id == current_user.id)
    ).scalar_one_or_none()

    if not settings_row:
        return ModelSettingsResponse()

    decrypted_hf_token = settings_row.huggingface_token
    if settings_row.huggingface_token:
        try:
            import base64 as _b64

            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF

            from backend.app.core.config import settings as _cfg

            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b"huggingface-token-encryption",
            )
            encryption_key = hkdf.derive(_cfg.SECRET_KEY.encode())
            fernet_key = Fernet(_b64.urlsafe_b64encode(encryption_key))
            decrypted_hf_token = fernet_key.decrypt(settings_row.huggingface_token.encode()).decode()
        except Exception:
            pass

    return {
        "inference_backend": settings_row.inference_backend,
        "huggingface_token": decrypted_hf_token,
        "auto_download": settings_row.auto_download,
        "max_concurrent_downloads": settings_row.max_concurrent_downloads,
    }


@router.put("/models/settings", response_model=ModelSettingsResponse)
async def update_model_settings(
    body: ModelSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user model settings."""
    settings_row = db.execute(
        select(UserModelSettings).where(UserModelSettings.user_id == current_user.id)
    ).scalar_one_or_none()

    if not settings_row:
        settings_row = UserModelSettings(user_id=current_user.id)
        db.add(settings_row)

    updates = body.model_dump(exclude_unset=True)

    if "huggingface_token" in updates and updates["huggingface_token"]:
        import base64 as _b64

        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        from backend.app.core.config import settings as _cfg

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"huggingface-token-encryption",
        )
        encryption_key = hkdf.derive(_cfg.SECRET_KEY.encode())
        fernet_key = Fernet(_b64.urlsafe_b64encode(encryption_key))
        updates["huggingface_token"] = fernet_key.encrypt(updates["huggingface_token"].encode()).decode()

    for key, value in updates.items():
        setattr(settings_row, key, value)

    db.commit()
    db.refresh(settings_row)

    decrypted_hf_token = settings_row.huggingface_token
    if settings_row.huggingface_token:
        try:
            import base64 as _b64

            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF

            from backend.app.core.config import settings as _cfg

            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b"huggingface-token-encryption",
            )
            encryption_key = hkdf.derive(_cfg.SECRET_KEY.encode())
            fernet_key = Fernet(_b64.urlsafe_b64encode(encryption_key))
            decrypted_hf_token = fernet_key.decrypt(settings_row.huggingface_token.encode()).decode()
        except Exception:
            pass

    return {
        "inference_backend": settings_row.inference_backend,
        "huggingface_token": decrypted_hf_token,
        "auto_download": settings_row.auto_download,
        "max_concurrent_downloads": settings_row.max_concurrent_downloads,
    }


@router.post("/models/catalogue/refresh", response_model=CatalogueRefreshResponse)
async def refresh_catalogue(
    current_user: User = Depends(get_current_user),
):
    """Refresh the Ollama catalog."""
    import asyncio

    from backend.app.services.intelligence.library_scraper import scrape_library_background
    from backend.app.services.intelligence.ollama_catalog import get_catalog_service

    asyncio.create_task(scrape_library_background())

    service = get_catalog_service()
    models, status = await service.fetch_catalog(force_refresh=True)

    return {"status": "ok", "models_added": len(models)}
