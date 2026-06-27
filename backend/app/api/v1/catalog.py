"""Model catalog browsing endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.model_catalog import ModelCatalog, ModelVariant
from backend.app.models.user import User
from backend.app.schemas.model import (
    AutocompleteResponse,
    CatalogSourceStatusResponse,
    HardwareInfoResponse,
    InferenceConfigResponse,
    ModelComparisonResponse,
    ModelDetailResponse,
    ModelListResponse,
    ModelSearchResponse,
    RecommendedModelsAllResponse,
    RecommendedModelsSingleResponse,
    WorkloadRecommendations,
)
from backend.app.services.awareness.hardware import detect_hardware as _detect_hardware_full
from backend.app.services.intelligence.llm.manager import LLMManager, llm_manager
from backend.app.services.intelligence.model_comparison import ModelComparisonService
from backend.app.services.intelligence.model_search import ModelSearchService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    model_type: str | None = None,
    downloaded_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List models from the unified Ollama catalog and available providers."""
    from backend.app.services.intelligence.ollama_catalog import get_ollama_catalog

    catalog_models, source_status = await get_ollama_catalog()

    available_models = await llm_manager.list_all_models()
    available_names = {m.name for m in available_models}

    catalog: list[dict[str, Any]] = []
    seen_bases: set[str] = set()
    for model in catalog_models:
        name = model.get("name", "")
        base = name.split(":")[0]

        if base in seen_bases:
            continue
        seen_bases.add(base)

        inferred_type = _infer_model_type(model)
        if model_type and inferred_type != model_type:
            continue

        downloaded = any(n.split(":")[0] == base for n in available_names)

        catalog.append(
            {
                "name": base,
                "display_name": base.replace("-", " ").title(),
                "provider": "ollama",
                "model_type": inferred_type,
                "parameter_count": _guess_param_count(base),
                "size_bytes": model.get("size", 0),
                "context_length": 4096,
                "capabilities": model.get("capabilities", ["chat"]),
                "description": model.get("description", f"Ollama model: {base}"),
                "downloaded": downloaded,
                "variants": _extract_variants(base, catalog),
                "hardware_requirements": _estimate_hardware(model.get("size", 0)),
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
        "type_counts": _compute_type_counts(catalog),
        "size_counts": _compute_size_counts(catalog),
        "catalog_status": CatalogSourceStatusResponse(**source_status.to_dict()),
    }


@router.get("/models/recommended", response_model=None)
async def recommended_models(
    workload: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return hardware-appropriate model recommendations."""
    from backend.app.services.awareness.hardware import detect_hardware as detect_hw
    from backend.app.services.intelligence.recommendation import WORKLOADS, RecommendationEngine

    hardware = detect_hw()
    engine = RecommendationEngine(hardware)

    from backend.app.services.intelligence.model_catalog import CatalogueManager

    catalogue_mgr = CatalogueManager(db)
    all_models = catalogue_mgr.get_all_catalogue()

    if workload and workload in WORKLOADS:
        recs = engine.recommend_for_workload(workload, all_models)
        return RecommendedModelsSingleResponse(
            hardware=hardware.to_dict(),
            workload=workload,
            recommendations=_format_recommendations(recs),  # type: ignore[arg-type]
        )
    else:
        all_recs = engine.recommend_all(all_models)
        formatted = {}
        for wl_id, recs in all_recs.items():
            formatted[wl_id] = WorkloadRecommendations(
                label=WORKLOADS[wl_id]["label"],  # type: ignore[arg-type]
                description=WORKLOADS[wl_id]["description"],  # type: ignore[arg-type]
                recommendations=_format_recommendations(recs),  # type: ignore[arg-type]
            )
        return RecommendedModelsAllResponse(
            hardware=hardware.to_dict(),
            workloads=formatted,
        )


@router.get("/models/hardware", response_model=HardwareInfoResponse)
async def detect_hardware(
    current_user: User = Depends(get_current_user),
):
    """Detect system hardware for model recommendations."""
    return _detect_hardware()


@router.get("/models/search", response_model=ModelSearchResponse)
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
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input")
    except Exception as e:
        logger.error("search_failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/models/compare", response_model=ModelComparisonResponse)
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
        logger.error("compare_failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models/autocomplete", response_model=AutocompleteResponse)
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
        logger.error("autocomplete_failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models/{model_id}", response_model=ModelDetailResponse)
async def get_model_detail(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed model info with variants."""
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


@router.get("/models/{model_id}/inference-config", response_model=InferenceConfigResponse)
async def get_inference_config(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get inference configuration for a model."""
    model = db.execute(select(ModelCatalog).where(ModelCatalog.model_id == model_id)).scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    config = {
        "model_id": model.model_id,
        "context_length": model.context_length_default,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "seed": -1,
        "num_predict": 2048,
        "num_ctx": model.context_length_default,
    }

    if model.capabilities:
        if "vision" in model.capabilities:
            config["image_resolution"] = 1024
        if "code" in model.capabilities:
            config["temperature"] = 0.3
            config["top_p"] = 0.95

    return config


# ── Helper functions ────────────────────────────────────────────────


def _infer_model_type(model: dict) -> str:
    """Infer model_type from catalog entry capabilities."""
    caps = model.get("capabilities", [])
    if "code" in caps and "chat" not in caps:
        return "code"
    if "vision" in caps:
        return "vision"
    if "embedding" in caps:
        return "embedding"
    return "chat"


def _guess_param_count(name: str) -> float | None:
    """Extract parameter count from model name. Delegates to LLMManager helper."""
    raw = LLMManager._guess_parameter_count(name)
    if raw is None:
        return None
    raw = raw.strip().upper()
    try:
        if raw.endswith("B"):
            return float(raw[:-1])
        elif raw.endswith("M"):
            return float(raw[:-1]) / 1000.0
        else:
            return float(raw)
    except (ValueError, IndexError):
        return None


def _compute_type_counts(catalog: list[dict]) -> dict[str, int]:
    """Compute model type counts from catalog entries."""
    counts: dict[str, int] = {}
    for entry in catalog:
        model_type = entry.get("model_type", "chat")
        counts[model_type] = counts.get(model_type, 0) + 1
    return counts


def _compute_size_counts(catalog: list[dict]) -> dict[str, int]:
    """Compute model size category counts from catalog entries."""
    counts: dict[str, int] = {"small": 0, "medium": 0, "large": 0}
    for entry in catalog:
        param_val = entry.get("parameter_count")
        tags = entry.get("tags", []) or []
        if param_val is None:
            if "lightweight" in tags:
                counts["small"] += 1
            else:
                counts["medium"] += 1
        elif param_val <= 4.0:
            counts["small"] += 1
        elif param_val <= 14.0:
            counts["medium"] += 1
        else:
            counts["large"] += 1
    return counts


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
    ram_gb = (size_bytes / (1024**3)) * 1.2
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
