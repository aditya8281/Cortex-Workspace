"""Indexing configuration API — CRUD and preview endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.indexing_config import IndexingConfig
from backend.app.models.user import User
from backend.app.schemas.indexing import IndexingConfigResponse, IndexingConfigSaveResponse, IndexingPreviewResponse
from backend.app.services.indexing_rules import IndexingRules

router = APIRouter()


class IndexingConfigPayload(BaseModel):
    name: str = "default"
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    max_file_size_bytes: int = 1_000_000
    follow_symlinks: bool = False
    sync_enabled: bool = True
    sync_interval_seconds: int = 300
    priority: int = 0


@router.get("/indexing/config", response_model=IndexingConfigResponse)
async def get_indexing_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(IndexingConfig).filter(IndexingConfig.user_id == current_user.id).first()
    if not config:
        return {"config": None, "defaults": True}
    return {
        "config": {
            "id": config.id,
            "name": config.name,
            "include_paths": config.include_paths,
            "exclude_paths": config.exclude_paths,
            "include_patterns": config.include_patterns,
            "exclude_patterns": config.exclude_patterns,
            "max_file_size_bytes": config.max_file_size_bytes,
            "follow_symlinks": config.follow_symlinks,
            "sync_enabled": config.sync_enabled,
            "sync_interval_seconds": config.sync_interval_seconds,
            "priority": config.priority,
        }
    }


@router.put("/indexing/config", response_model=IndexingConfigSaveResponse)
async def update_indexing_config(
    payload: IndexingConfigPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = (
        db.query(IndexingConfig)
        .filter(
            IndexingConfig.user_id == current_user.id,
            IndexingConfig.name == payload.name,
        )
        .first()
    )
    if not config:
        config = IndexingConfig(user_id=current_user.id, name=payload.name)
        db.add(config)

    for field, value in payload.model_dump().items():
        setattr(config, field, value)
    db.commit()
    return {"status": "saved"}


@router.post("/indexing/preview", response_model=IndexingPreviewResponse)
async def preview_indexing(
    repo_path: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview what would be indexed for a given path."""
    config = db.query(IndexingConfig).filter(IndexingConfig.user_id == current_user.id).first()
    rules = IndexingRules(config)
    stats = rules.get_stats(repo_path)
    return stats
