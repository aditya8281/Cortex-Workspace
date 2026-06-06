from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.ai.model_downloads import model_download_manager
from backend.app.ai.model_registry import ModelRegistry
from backend.app.core.db import get_db
from backend.app.core.paths import PROJECT_ROOT
from backend.app.models.user_settings import UserSettings

router = APIRouter()
CONFIG_PATH = PROJECT_ROOT / ".cortex" / "model_control_config.json"


class DownloadRequest(BaseModel):
    model: str = Field(..., min_length=1)


class ModelConfig(BaseModel):
    active_profile: str = "Balanced"
    preferred_model: str = "Auto"
    local_only: bool = False
    auto_download: bool = True
    gpu_acceleration: bool = True
    context_strategy: str = "balanced"
    selected_model: str = "Auto"


def _default_config() -> dict[str, Any]:
    return ModelConfig().model_dump()


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return _default_config()
    try:
        return {**_default_config(), **json.loads(CONFIG_PATH.read_text(encoding="utf-8"))}
    except Exception:
        return _default_config()


def _save_config(config: dict[str, Any]) -> dict[str, Any]:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    return config


@router.get("/api/models/local")
def list_local_models(db: Session = Depends(get_db)):
    ModelRegistry.seed_if_empty(db)
    local_models: list[dict[str, Any]] = []

    try:
        installed = model_download_manager.list_jobs()
    except Exception:
        installed = []

    try:
        local_entities = asyncio.run(ModelRegistry.get_local_models())
        local_models = [
            entity.model_dump() if hasattr(entity, "model_dump") else dict(entity)
            for entity in local_entities
        ]
    except Exception:
        local_models = []

    if not local_models:
        try:
            url_models = asyncio.run(ModelRegistry.list_models(db))
            local_models = [model for model in url_models if model.get("is_local")]
        except Exception:
            local_models = []

    jobs_by_model = {job.get("model"): job for job in installed}
    hardware = {}
    try:
        from backend.app.api.v1.models import get_hardware

        hardware = get_hardware()
    except Exception:
        hardware = {}

    enriched = []
    for model in local_models:
        model_name = model.get("name") or model.get("id") or "unknown"
        job = jobs_by_model.get(model_name)
        enriched.append(
            {
                **model,
                "size_label": model.get("size") or model.get("parameters") or "unknown",
                "vram_label": model.get("vram_estimate") or "N/A",
                "download_status": job.get("status") if job else "installed",
                "download_percent": job.get("percent", 100) if job else 100,
                "download_job_id": job.get("id") if job else None,
                "hardware": hardware,
            }
        )

    return enriched


@router.post("/api/models/download")
def download_model(payload: DownloadRequest):
    return model_download_manager.start_download(payload.model)


@router.get("/api/models/downloads")
def list_downloads():
    return model_download_manager.list_jobs()


@router.get("/api/models/config")
def get_model_config(db: Session = Depends(get_db)):
    config = _load_config()

    try:
        settings_row = db.query(UserSettings).first()
        if settings_row and settings_row.selected_model:
            config["selected_model"] = settings_row.selected_model
            if config.get("preferred_model") == "Auto":
                config["preferred_model"] = settings_row.selected_model
    except Exception:
        pass

    return config


@router.put("/api/models/config")
def update_model_config(payload: dict[str, Any], db: Session = Depends(get_db)):
    current = _load_config()
    next_config = {
        **current,
        **payload,
    }

    _save_config(next_config)

    try:
        settings_row = db.query(UserSettings).first()
        if settings_row:
            if "selected_model" in payload:
                settings_row.selected_model = str(payload["selected_model"])
            if "llm_model" in payload:
                settings_row.llm_model = str(payload["llm_model"])
            db.commit()
    except Exception:
        db.rollback()

    return next_config
