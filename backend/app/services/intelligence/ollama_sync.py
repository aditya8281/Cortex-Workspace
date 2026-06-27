"""Ollama auto-detect sync service.

Queries Ollama's /api/tags to detect locally installed models
and syncs their download status to the database.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    matched: int = 0
    created: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)


def _guess_quant_from_tag(tag: str) -> str:
    """Guess quantization level from Ollama tag."""
    tag_lower = tag.lower()
    if "q4_k_m" in tag_lower:
        return "Q4_K_M"
    if "q4_k_s" in tag_lower:
        return "Q4_K_S"
    if "q5_k_m" in tag_lower:
        return "Q5_K_M"
    if "q8_0" in tag_lower:
        return "Q8_0"
    if "q3_k" in tag_lower:
        return "Q3_K"
    if "fp16" in tag_lower or "f16" in tag_lower:
        return "FP16"
    if "q6_k" in tag_lower:
        return "Q6_K"
    return "default"


def _extract_param_count(model_name: str) -> float:
    """Extract parameter count from model name (e.g., 'llama3.1:8b' -> 8.0)."""
    match = re.search(r"(\d+\.?\d*)[bB]", model_name)
    if match:
        return float(match.group(1))
    return 7.0


class OllamaSyncService:
    """Syncs Ollama's locally installed models to the Cortex database."""

    async def sync_installed_models(self, db: Session) -> SyncResult:
        result = SyncResult()

        # 1. Query Ollama for installed models
        installed_models = await self._fetch_installed(result)
        if installed_models is None:
            return result

        installed_tags = {m["name"] for m in installed_models}
        installed_by_tag = {m["name"]: m for m in installed_models}

        try:
            # 2. Match existing variants by ollama_tag
            existing_variants = (
                db.execute(
                    select(ModelVariant).where(
                        ModelVariant.ollama_tag.isnot(None),
                        ModelVariant.ollama_tag.in_(list(installed_tags)),
                    )
                )
                .scalars()
                .all()
            )

            matched_tags = set()
            for variant in existing_variants:
                if not variant.downloaded:
                    variant.downloaded = True
                    variant.last_downloaded_at = datetime.now(timezone.utc)
                    result.matched += 1
                matched_tags.add(variant.ollama_tag)

            # 3. Create unknown models
            unmatched_tags = installed_tags - matched_tags
            for tag in unmatched_tags:
                model_info = installed_by_tag[tag]
                base_name = tag.split(":")[0]

                # Find or create ModelCatalog entry
                catalog = db.execute(
                    select(ModelCatalog).where(ModelCatalog.model_id == base_name)
                ).scalar_one_or_none()

                if catalog is None:
                    catalog = ModelCatalog(
                        model_id=base_name,
                        display_name=base_name.replace("-", " ").title(),
                        family="unknown",
                        provider="ollama",
                        parameter_count=_extract_param_count(base_name),
                    )
                    db.add(catalog)
                    db.flush()
                    result.created += 1

                # Create variant
                variant = ModelVariant(
                    model_catalog_id=catalog.id,
                    variant_id=tag,
                    ollama_tag=tag,
                    quantization=_guess_quant_from_tag(tag),
                    size_bytes=model_info.get("size", 0),
                    downloaded=True,
                    last_downloaded_at=datetime.now(timezone.utc),
                )
                db.add(variant)
                result.created += 1

            # 4. Detect deletions
            downloaded_variants = (
                db.execute(
                    select(ModelVariant).where(
                        ModelVariant.downloaded,
                        ModelVariant.ollama_tag.isnot(None),
                    )
                )
                .scalars()
                .all()
            )

            for variant in downloaded_variants:
                if variant.ollama_tag not in installed_tags:
                    variant.downloaded = False
                    result.deleted += 1

            db.commit()
        except Exception:
            db.rollback()
            raise
        return result

    async def _fetch_installed(self, result: SyncResult) -> list[dict] | None:
        """Fetch installed models from Ollama. Returns None on failure."""
        try:
            async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5.0) as client:
                resp = await client.get("/api/tags")
                resp.raise_for_status()
                return resp.json().get("models", [])
        except Exception as e:
            logger.warning("Failed to fetch Ollama models: %s", e)
            result.errors.append(str(e))
            return None
