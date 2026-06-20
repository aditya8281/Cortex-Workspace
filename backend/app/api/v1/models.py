from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.catalogue import CatalogueManager
from backend.app.services.hardware import detect_hardware as _detect_hardware_full
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
    workload: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Return hardware-appropriate model recommendations."""
    from backend.app.services.hardware import detect_hardware as detect_hw
    from backend.app.services.recommendation import WORKLOADS, RecommendationEngine

    hardware = detect_hw()
    engine = RecommendationEngine(hardware)

    # Get all catalogue models
    db = next(get_db())
    catalogue_mgr = CatalogueManager(db)
    all_models = catalogue_mgr.get_all_catalogue()

    if workload and workload in WORKLOADS:
        # Single workload
        recs = engine.recommend_for_workload(workload, all_models)
        return {
            "hardware": hardware.to_dict(),
            "workload": workload,
            "recommendations": _format_recommendations(recs),
        }
    else:
        # All workloads
        all_recs = engine.recommend_all(all_models)
        formatted = {}
        for wl_id, recs in all_recs.items():
            formatted[wl_id] = {
                "label": WORKLOADS[wl_id]["label"],
                "description": WORKLOADS[wl_id]["description"],
                "recommendations": _format_recommendations(recs),
            }
        return {
            "hardware": hardware.to_dict(),
            "workloads": formatted,
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
    """Detect system hardware — delegates to hardware service."""
    profile = _detect_hardware_full()
    return profile.to_dict()


def _format_recommendations(recs: list) -> list[dict]:
    """Format recommendations for API response."""
    result = []
    for rec in recs:
        perf = rec.performance
        variant = rec.variant
        model = rec.catalog_entry
        result.append({
            "model_id": model.model_id,
            "display_name": model.display_name,
            "family": model.family,
            "parameter_count": model.parameter_count,
            "capabilities": model.capabilities or [],
            "description": model.description,
            "score": round(rec.score, 1),
            "variant": {
                "quantization": variant.quantization if variant else None,
                "size_gb": round(variant.size_gb, 1) if variant else None,
                "vram_required_gb": round(variant.vram_required_gb, 1) if variant else None,
                "quality_score": round(variant.quality_score, 1) if variant else None,
            } if variant else None,
            "performance": {
                "tokens_per_second": round(perf.tokens_per_second, 1) if perf.tokens_per_second else None,
                "prompt_eval_tps": round(perf.prompt_eval_tps, 1) if perf.prompt_eval_tps else None,
                "memory_usage_gb": round(perf.memory_usage_gb, 1),
                "vram_usage_gb": round(perf.vram_usage_gb, 1),
                "quantization_quality": perf.quantization_quality,
                "quality_notes": perf.quality_notes,
                "speed_rating": perf.speed_rating,
                "fit_rating": perf.fit_rating,
                "context_length_max": perf.context_length_max,
            } if perf else None,
            "explanation": {
                "why": rec.why_recommended,
                "tradeoff": rec.quality_tradeoff,
                "suitability": rec.hardware_suitability,
            },
        })
    return result
