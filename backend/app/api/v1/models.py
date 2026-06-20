from __future__ import annotations

import logging
from pathlib import Path

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.db import get_current_user, get_db
from backend.app.models.model_catalog import ModelCatalog, ModelVariant
from backend.app.models.user import User
from backend.app.services.catalogue import CatalogueManager
from backend.app.services.hardware import detect_hardware as _detect_hardware_full
from backend.app.services.llm.manager import MODEL_CATALOG, LLMManager, llm_manager
from backend.app.services.model_comparison import ModelComparisonService
from backend.app.services.model_downloader import model_downloader
from backend.app.services.model_search import ModelSearchService
from backend.app.services.sync_service import SyncService

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


@router.get("/models/usage/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get model usage statistics."""
    from backend.app.services.usage_tracker import UsageTracker

    tracker = UsageTracker(db)
    return tracker.get_usage_stats()


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


@router.get("/models/installed")
async def list_installed_models(
    current_user: User = Depends(get_current_user),
):
    """List installed/downloaded model variants."""
    db = next(get_db())
    catalogue_mgr = CatalogueManager(db)

    # Get Ollama installed models
    try:
        import httpx

        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5.0) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            installed = resp.json().get("models", [])
    except Exception:
        installed = []

    installed_names = {m["name"] for m in installed}

    # Get all catalogue entries and mark downloaded ones
    all_models = catalogue_mgr.get_all_catalogue()
    result = []
    for model in all_models:
        variants = []
        for tag in installed_names:
            base = tag.split(":")[0]
            if base in model.model_id or model.model_id.startswith(base):
                variants.append(
                    {
                        "variant_id": tag,
                        "quantization": _guess_quant_from_tag(tag),
                        "size_bytes": next((m.get("size", 0) for m in installed if m["name"] == tag), 0),
                        "size_gb": round(
                            next((m.get("size", 0) for m in installed if m["name"] == tag), 0) / (1024**3), 1
                        ),
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


@router.get("/models/search")
async def search_models(
    q: str = "",
    capabilities: str | None = None,
    min_params: float | None = None,
    max_params: float | None = None,
    provider: str | None = None,
    family: str | None = None,
    sort: str = "relevance",
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search models by query and filters."""
    try:
        service = ModelSearchService(db)
        cap_list = [c.strip() for c in capabilities.split(",")] if capabilities else None

        if q:
            models = service.search(q, limit=limit)
        else:
            models = service.filter(
                capabilities=cap_list,
                min_params=min_params,
                max_params=max_params,
                provider=provider,
                family=family,
                sort=sort,
                limit=limit,
            )

        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "display_name": m.display_name,
                    "family": m.family,
                    "provider": m.provider,
                    "parameter_count": m.parameter_count,
                    "architecture": m.architecture,
                    "context_length": m.context_length_default,
                    "capabilities": m.capabilities or [],
                    "description": m.description,
                    "tags": m.tags or [],
                }
                for m in models
            ],
            "total_count": len(models),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/models/compare")
async def compare_models(
    model_ids: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare 2-5 models side-by-side."""
    try:
        if len(model_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 model IDs required")
        if len(model_ids) > 5:
            raise HTTPException(status_code=400, detail="At most 5 model IDs allowed")

        models = []
        for mid in model_ids:
            m = db.execute(select(ModelCatalog).where(ModelCatalog.model_id == mid)).scalar_one_or_none()
            if not m:
                raise HTTPException(status_code=404, detail=f"Model {mid} not found")
            models.append(m)

        service = ModelComparisonService()
        result = service.compare(models)

        return {
            "models": result.models,
            "winner_model": result.winner_model,
            "dimension_wins": result.dimension_wins,
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "display_name": d.display_name,
                    "values": d.values,
                    "winner": d.winner,
                    "higher_is_better": d.higher_is_better,
                }
                for d in result.dimensions
            ],
            "summary": result.summary,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("compare_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/models/sync")
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
            "job_id": job.id,
            "status": job.status,
            "models_discovered": job.models_discovered,
            "models_added": job.models_added,
            "models_updated": job.models_updated,
            "error_message": job.error_message,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("sync_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models/sync/status")
async def sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sync job history."""
    try:
        service = SyncService(db)
        return {"jobs": service.get_sync_status()}
    except Exception as e:
        logger.error("sync_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models/autocomplete")
async def autocomplete_models(
    q: str = "",
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Autocomplete model names."""
    try:
        service = ModelSearchService(db)
        suggestions = service.autocomplete(q, limit=limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error("autocomplete_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


def _guess_quant_from_tag(tag: str) -> str:
    """Guess quantization from Ollama tag."""
    tag_lower = tag.lower()
    for q in ["q4_k_m", "q5_k_m", "q8_0", "q4_k_s", "q6_k", "f16", "f32", "q4_0", "q3_k_m"]:
        if q in tag_lower:
            return q.upper()
    return "UNKNOWN"


@router.get("/models/storage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
):
    """Get storage usage breakdown."""
    models_dir = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "models"

    # Disk usage
    try:
        disk = psutil.disk_usage(".")
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
    except Exception:
        total_gb = used_gb = free_gb = 0

    # Models directory size
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
        "models": [],  # Per-model breakdown would need Ollama API
    }


@router.get("/models/{model_id}")
async def get_model_detail(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get detailed model info with variants."""
    db = next(get_db())

    model = db.execute(select(ModelCatalog).where(ModelCatalog.model_id == model_id)).scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    variants = db.execute(select(ModelVariant).where(ModelVariant.model_catalog_id == model.id)).scalars().all()

    return {
        "model_id": model.model_id,
        "display_name": model.display_name,
        "family": model.family,
        "parameter_count": model.parameter_count,
        "architecture": model.architecture,
        "context_length_default": model.context_length_default,
        "context_length_max": model.context_length_max,
        "capabilities": model.capabilities or [],
        "license": model.license,
        "recommended_use_cases": model.recommended_use_cases or [],
        "description": model.description,
        "tags": model.tags or [],
        "benchmarks": model.benchmarks,
        "variants": [
            {
                "variant_id": v.variant_id,
                "quantization": v.quantization,
                "quantization_level": v.quantization_level,
                "parameter_count": v.parameter_count,
                "size_bytes": v.size_bytes,
                "size_gb": round(v.size_gb, 1) if v.size_gb else None,
                "vram_required_gb": round(v.vram_required_gb, 1) if v.vram_required_gb else None,
                "quality_score": round(v.quality_score, 1) if v.quality_score else None,
                "downloaded": v.downloaded,
                "ollama_tag": v.ollama_tag,
            }
            for v in variants
        ],
    }


@router.post("/models/catalogue/refresh")
async def refresh_catalogue(
    current_user: User = Depends(get_current_user),
):
    """Force refresh the model catalogue."""
    db = next(get_db())
    catalogue_mgr = CatalogueManager(db)

    # Re-seed curated models
    added = catalogue_mgr.seed_curated_models()

    return {"status": "refreshed", "models_added": added}


@router.get("/models/updates")
async def check_model_updates(
    current_user: User = Depends(get_current_user),
):
    """Check for available model updates."""
    # For now, return empty — this will be implemented in lifecycle management
    return {"updates": []}


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
        result.append(
            {
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
                }
                if variant
                else None,
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
                }
                if perf
                else None,
                "explanation": {
                    "why": rec.why_recommended,
                    "tradeoff": rec.quality_tradeoff,
                    "suitability": rec.hardware_suitability,
                },
            }
        )
    return result
