"""Model download management endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.config import settings
from backend.app.core.db import get_current_user
from backend.app.models.interaction.user import User
from backend.app.schemas.intelligence.model import (
    CancelDownloadResponse,
    DeleteModelResponse,
    DownloadHistoryResponse,
    DownloadModelResponse,
    DownloadProgressResponse,
    DownloadQueueResponse,
    InstalledModelsResponse,
    SyncInstalledResponse,
)
from backend.app.services.download.downloader import model_downloader

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models/installed", response_model=InstalledModelsResponse)
async def list_installed_models(
    current_user: User = Depends(get_current_user),
):
    """List installed/downloaded models from Ollama local API.

    Reads directly from localhost:11434/api/tags — no DB required.
    """
    try:
        import httpx

        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5.0) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            installed = resp.json().get("models", [])
    except Exception as e:
        logger.warning("Failed to fetch installed models from Ollama: %s", e)
        installed = []

    result = []
    for m in installed:
        name = m.get("name", "")
        details = m.get("details", {})
        size_bytes = m.get("size", 0)
        result.append(
            {
                "model_id": name,
                "display_name": name.replace("-", " ").title(),
                "family": details.get("family", ""),
                "parameter_count": _parse_param_count(details.get("parameter_size", "")),
                "capabilities": [],
                "variants": [
                    {
                        "variant_id": name,
                        "quantization": details.get("quantization_level", "unknown"),
                        "size_bytes": size_bytes,
                        "size_gb": round(size_bytes / (1024**3), 1) if size_bytes else 0,
                        "downloaded": True,
                        "parameter_count": _parse_param_count(details.get("parameter_size", "")),
                        "quality_score": 90.0,
                    }
                ],
            }
        )

    return {"models": result, "installed_count": len(result)}


@router.post("/models/installed/sync", response_model=SyncInstalledResponse)
async def sync_installed_models(
    current_user: User = Depends(get_current_user),
):
    """Sync locally installed Ollama models to the database."""
    from backend.app.core.db import get_db
    from backend.app.services.intelligence.ollama_sync import OllamaSyncService

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


def _parse_param_count(raw: str) -> float | None:
    """Parse '3.2B', '1B', '70B', '480M' etc. from Ollama details."""
    if not raw:
        return None
    raw = raw.strip().upper()
    try:
        if raw.endswith("B"):
            return float(raw[:-1])
        if raw.endswith("M"):
            return float(raw[:-1]) / 1000.0
        return float(raw)
    except (ValueError, IndexError):
        return None


@router.get("/models/downloads/queue", response_model=DownloadQueueResponse)
async def get_download_queue(
    current_user: User = Depends(get_current_user),
):
    """Get current download queue status."""
    from backend.app.services.download.downloader import download_manager

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
    from backend.app.services.download.downloader import download_manager

    records = download_manager.list_downloads()

    history = []
    for rec in records:
        if rec["status"] in ("completed", "failed", "cancelled"):
            history.append(
                {
                    "job_id": rec["download_id"],
                    "model_id": rec["model_name"],
                    "status": rec["status"],
                    "progress": rec["progress"] if rec["status"] != "completed" else 1.0,
                    "downloaded_bytes": rec.get("bytes_downloaded", 0),
                    "total_bytes": rec.get("total_bytes", 0),
                    "error": rec.get("error_message"),
                    "completed_at": rec.get("completed_at"),
                    "created_at": rec.get("created_at"),
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
        resp = await client.request("DELETE", "/api/delete", json={"name": model_name})
        resp.raise_for_status()
    return {"status": "deleted", "model": model_name}
