"""Model download management endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.config import settings
from backend.app.core.db import get_current_user
from backend.app.models.user import User
from backend.app.schemas.model import (
    CancelDownloadResponse,
    DeleteModelResponse,
    DownloadHistoryResponse,
    DownloadModelResponse,
    DownloadProgressResponse,
    DownloadQueueResponse,
    InstalledModelsResponse,
    SyncInstalledResponse,
)
from backend.app.services.model_downloader import model_downloader

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models/installed", response_model=InstalledModelsResponse)
async def list_installed_models(
    current_user: User = Depends(get_current_user),
):
    """List installed/downloaded model variants."""
    try:
        import httpx

        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5.0) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            installed = resp.json().get("models", [])
    except Exception as e:
        logger.warning("Failed to fetch installed models from Ollama: %s", e)
        installed = []

    installed_names = {m["name"] for m in installed}

    from backend.app.core.db import get_db
    from backend.app.services.catalogue import CatalogueManager

    db = next(get_db())
    try:
        catalogue_mgr = CatalogueManager(db)
        all_models = catalogue_mgr.get_all_catalogue()
    finally:
        db.close()

    result = []
    for model in all_models:
        variants = []
        for tag in installed_names:
            base = tag.split(":")[0]
            if base in model.model_id or model.model_id.startswith(base):
                size_bytes = next((m.get("size", 0) for m in installed if m["name"] == tag), 0)
                variants.append(
                    {
                        "variant_id": tag,
                        "quantization": _guess_quant_from_tag(tag),
                        "size_bytes": size_bytes,
                        "size_gb": round(size_bytes / (1024**3), 1),
                        "downloaded": True,
                        "parameter_count": model.parameter_count,
                        "quality_score": 90.0,
                    }
                )
        if variants:
            result.append(
                {
                    "model_id": model.model_id,
                    "display_name": model.display_name,
                    "family": model.family,
                    "parameter_count": model.parameter_count,
                    "capabilities": model.capabilities or [],
                    "variants": variants,
                }
            )

    return {"models": result, "installed_count": len(result)}


@router.post("/models/installed/sync", response_model=SyncInstalledResponse)
async def sync_installed_models(
    current_user: User = Depends(get_current_user),
):
    """Sync locally installed Ollama models to the database."""
    from backend.app.core.db import get_db
    from backend.app.services.ollama_sync import OllamaSyncService

    db = next(get_db())
    try:
        service = OllamaSyncService()
        result = await service.sync_installed_models(db)
        return result
    finally:
        db.close()


def _guess_quant_from_tag(tag: str) -> str:
    """Guess quantization from Ollama tag."""
    tag_lower = tag.lower()
    for q in ["q4_k_m", "q5_k_m", "q8_0", "q4_k_s", "q6_k", "f16", "f32", "q4_0", "q3_k_m"]:
        if q in tag_lower:
            return q.upper()
    return "UNKNOWN"


@router.get("/models/downloads/queue", response_model=DownloadQueueResponse)
async def get_download_queue(
    current_user: User = Depends(get_current_user),
):
    """Get current download queue status."""
    from backend.app.services.model_downloader import download_manager

    records = download_manager.list_downloads()

    active = []
    queued = []
    completed = []
    failed = []

    for rec in records:
        rec_dict = {
            "job_id": rec["download_id"],
            "model_id": rec["model_name"],
            "status": rec["status"],
            "progress": rec["progress"],
            "speed_bytes_sec": rec["speed_bytes_sec"],
            "downloaded_bytes": rec.get("bytes_downloaded", 0),
            "total_bytes": rec.get("total_bytes", 0),
            "eta_seconds": rec["eta_seconds"],
            "queue_position": None,
            "error": rec["error_message"],
        }

        if rec["status"] == "downloading":
            active.append(rec_dict)
        elif rec["status"] == "queued":
            queued.append(rec_dict)
        elif rec["status"] == "completed":
            completed.append(rec_dict)
        elif rec["status"] in ("failed", "cancelled"):
            failed.append(rec_dict)

    for i, job in enumerate(queued):
        job["queue_position"] = i + 1

    return {
        "active": active,
        "queued": queued,
        "completed": completed,
        "failed": failed,
    }


@router.get("/models/downloads/history", response_model=DownloadHistoryResponse)
async def get_download_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """Get download history."""
    from backend.app.services.model_downloader import download_manager

    records = download_manager.list_downloads()

    history = []
    for rec in records:
        if rec.status.value in ("completed", "failed", "cancelled"):
            history.append(
                {
                    "job_id": rec.download_id,
                    "model_id": rec.model_name,
                    "status": rec.status.value,
                    "progress": rec.progress if rec.status.value != "completed" else 1.0,
                    "downloaded_bytes": rec.bytes_downloaded,
                    "total_bytes": rec.total_bytes,
                    "error": rec.error_message,
                    "completed_at": rec.completed_at,
                    "created_at": rec.created_at,
                }
            )

    history.sort(key=lambda x: x.get("completed_at") or 0, reverse=True)

    return {"history": history[:limit]}


@router.post("/models/{model_name}/download", response_model=DownloadModelResponse)
async def download_model(
    model_name: str,
    variant: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Start downloading a model."""
    try:
        result = await model_downloader.download_model(model_name, [], variant=variant)
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Model not found")


@router.get("/models/{model_name}/progress", response_model=DownloadProgressResponse)
async def download_progress(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get download progress for a model."""
    progress = model_downloader.get_progress(model_name)
    return {"model": model_name, "progress": progress}


@router.post("/models/{model_name}/cancel", response_model=CancelDownloadResponse)
async def cancel_download(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel an active download."""
    cancelled = await model_downloader.cancel_download(model_name)
    return {"cancelled": cancelled}


@router.delete("/models/{model_name}", response_model=DeleteModelResponse)
async def delete_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an Ollama model."""
    import httpx

    async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=30.0) as client:
        resp = await client.delete("/api/delete", json={"name": model_name})
        resp.raise_for_status()
    return {"status": "deleted", "model": model_name}
