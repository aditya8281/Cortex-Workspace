from __future__ import annotations
import logging

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.llm.manager import llm_manager, MODEL_CATALOG

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

    return {
        "models": catalog,
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
    recommended = [
        m for m in MODEL_CATALOG
        if m.get("recommended")
        and hardware["ram_gb"] >= m.get("hardware_requirements", {}).get("min_ram_gb", 0)
    ]
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


def _detect_hardware() -> dict:
    """Detect system hardware (sync — called from sync endpoint)."""
    ram_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count() or 1

    gpu_info: dict = {"available": False, "name": None, "vram_gb": 0}
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
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
            }
    except Exception:
        pass

    return {
        "ram_gb": round(ram_gb, 1),
        "cpu_count": cpu_count,
        "gpu": gpu_info,
    }
