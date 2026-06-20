from __future__ import annotations

import logging

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.llm.manager import MODEL_CATALOG, LLMManager, llm_manager
from backend.app.services.model_downloader import model_downloader

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models")
async def list_models(
    model_type: str | None = None,
    downloaded_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List models from catalog and available providers."""
    # Merge catalog with provider-detected models
    available_models = await llm_manager.list_all_models()
    available_names = {m.name for m in available_models}

    catalog = list(MODEL_CATALOG)
    if model_type:
        catalog = [m for m in catalog if m.get("model_type") == model_type]

    # Enrich catalog entries with provider status
    for entry in catalog:
        entry["downloaded"] = entry["name"] in available_names

    # Merge in dynamic Ollama models not already in static catalog
    dynamic = await llm_manager.fetch_ollama_catalog()
    static_names = {m["name"] for m in catalog}
    for dm in dynamic:
        if dm.name and dm.name not in static_names:
            # Infer model_type from capabilities
            inferred_type = "chat"
            if "code" in dm.capabilities and "chat" not in dm.capabilities:
                inferred_type = "code"
            elif "vision" in dm.capabilities:
                inferred_type = "vision"
            elif "embedding" in dm.capabilities:
                inferred_type = "embedding"

            catalog.append(
                {
                    "name": dm.name,
                    "display_name": dm.name.split(":")[0].replace("-", " ").title(),
                    "provider": "ollama",
                    "model_type": inferred_type,
                    "parameter_count": _guess_param_count(dm.name),
                    "size_bytes": dm.size_bytes,
                    "context_length": dm.context_length,
                    "capabilities": dm.capabilities,
                    "description": dm.description,
                    "downloaded": dm.name in available_names,
                    "variants": _extract_variants(dm.name, catalog),
                    "hardware_requirements": _estimate_hardware(dm.size_bytes),
                }
            )

    return {
        "models": catalog,
        "total_count": len(catalog),
        "downloaded_count": sum(1 for m in catalog if m.get("downloaded")),
        "available_from_providers": [
            {
                "name": m.name,
                "size_bytes": m.size_bytes,
                "context_length": m.context_length,
                "capabilities": m.capabilities,
            }
            for m in available_models
        ],
    }


@router.get("/models/recommended")
async def recommended_models(
    current_user: User = Depends(get_current_user),
):
    """Return hardware-appropriate model recommendations."""
    hardware = _detect_hardware()

    available_models = await llm_manager.list_all_models()
    available_names = {m.name for m in available_models}

    recommended = []
    seen_names = set()

    for m in MODEL_CATALOG:
        if m.get("recommended") and hardware["ram_gb"] >= m.get("hardware_requirements", {}).get("min_ram_gb", 0):
            model_dict = dict(m)
            model_dict["source"] = "catalog"
            model_dict["downloaded"] = m["name"] in available_names
            recommended.append(model_dict)
            seen_names.add(m["name"])

    dynamic_models = await llm_manager.fetch_ollama_catalog()
    for dm in dynamic_models:
        if dm.name and dm.name not in seen_names and dm.name in available_names:
            if hardware["ram_gb"] >= 4:
                # Infer type from capabilities
                inferred_type = "chat"
                if "code" in dm.capabilities and "chat" not in dm.capabilities:
                    inferred_type = "code"
                elif "vision" in dm.capabilities:
                    inferred_type = "vision"
                elif "embedding" in dm.capabilities:
                    inferred_type = "embedding"
                model_dict = {
                    "name": dm.name,
                    "display_name": dm.name.split(":")[0].replace("-", " ").title(),
                    "provider": "ollama",
                    "model_type": inferred_type,
                    "parameter_count": _guess_param_count(dm.name),
                    "size_bytes": dm.size_bytes,
                    "context_length": dm.context_length,
                    "capabilities": dm.capabilities,
                    "description": dm.description,
                    "hardware_requirements": _estimate_hardware(dm.size_bytes),
                    "source": "system",
                    "downloaded": True,
                }
                recommended.append(model_dict)

    return {
        "hardware": hardware,
        "recommended": recommended,
    }


@router.get("/models/hardware")
async def detect_hardware(
    current_user: User = Depends(get_current_user),
):
    """Detect system hardware for model recommendations."""
    return _detect_hardware()


@router.get("/models/health")
async def llm_health(
    current_user: User = Depends(get_current_user),
):
    """Check health of all LLM providers."""
    return await llm_manager.health_check()


@router.get("/models/metrics")
async def llm_metrics(
    current_user: User = Depends(get_current_user),
):
    """Return token usage and request metrics."""
    return llm_manager.get_metrics()


@router.post("/models/{model_name}/download")
async def download_model(
    model_name: str,
    variant: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Start downloading a model."""
    try:
        result = await model_downloader.download_model(model_name, MODEL_CATALOG, variant=variant)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/models/{model_name}/progress")
async def download_progress(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get download progress for a model."""
    progress = model_downloader.get_progress(model_name)
    return {"model": model_name, "progress": progress}


@router.post("/models/{model_name}/cancel")
async def cancel_download(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel an active download."""
    cancelled = await model_downloader.cancel_download(model_name)
    return {"cancelled": cancelled}


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an Ollama model."""
    import httpx

    async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL) as client:
        resp = await client.delete("/api/delete", json={"name": model_name})
        resp.raise_for_status()
    return {"status": "deleted", "model": model_name}


def _guess_param_count(name: str) -> str | None:
    """Extract parameter count from model name. Delegates to LLMManager helper."""
    return LLMManager._guess_parameter_count(name)


def _extract_variants(model_name: str, existing_catalog: list[dict]) -> list[str]:
    """Find sibling variants of a model already present in the catalog."""
    base = model_name.split(":")[0]
    variants: list[str] = []
    for entry in existing_catalog:
        if entry["name"].split(":")[0] == base:
            variants.append(entry["name"])
    if model_name not in variants:
        variants.append(model_name)
    return sorted(set(variants))


def _estimate_hardware(size_bytes: int) -> dict:
    """Rough RAM requirements based on model size in bytes."""
    if not size_bytes:
        return {"min_ram_gb": 4, "recommended_ram_gb": 8}
    ram_gb = (size_bytes / (1024**3)) * 1.2  # ~20% overhead for inference
    return {
        "min_ram_gb": max(2, int(ram_gb)),
        "recommended_ram_gb": max(4, int(ram_gb * 1.5)),
    }


def _detect_hardware() -> dict:
    """Detect system hardware (sync — called from sync endpoint)."""
    ram = psutil.virtual_memory()
    ram_gb = ram.total / (1024**3)
    ram_used_gb = ram.used / (1024**3)
    ram_percent = ram.percent
    cpu_count = psutil.cpu_count() or 1
    cpu_percent = psutil.cpu_percent(interval=0.1)

    gpu_info: dict = {"available": False, "name": None, "vram_gb": 0, "vram_used_gb": 0, "gpu_percent": 0}
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(", ")
            gpu_info = {
                "available": True,
                "name": parts[0],
                "vram_gb": float(parts[1]) / 1024,
                "vram_used_gb": float(parts[2]) / 1024,
                "gpu_percent": float(parts[3]),
            }
    except Exception:
        pass

    return {
        "ram_gb": round(ram_gb, 1),
        "ram_used_gb": round(ram_used_gb, 1),
        "ram_percent": ram_percent,
        "cpu_count": cpu_count,
        "cpu_percent": cpu_percent,
        "gpu": gpu_info,
    }
