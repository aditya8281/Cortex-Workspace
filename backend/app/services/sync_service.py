"""Background sync service for the model catalog.

Discovers models from the unified Ollama catalog and registered providers,
then upserts them into ModelCatalog.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.model_catalog import ModelCatalog, Provider, SyncJob
from backend.app.services.providers.base import ProviderModelInfo
from backend.app.services.providers.registry import provider_registry

logger = structlog.get_logger()


class SyncService:
    """Orchestrates model catalog synchronization across providers."""

    def __init__(self, db: Session) -> None:
        self.db = db

    async def sync_library(self, provider_name: str | None = None) -> SyncJob:
        """Run a full sync: discover models from providers and upsert into catalog.

        Uses the unified Ollama catalog (three-source pipeline) for Ollama models
        and registered provider adapters for other providers.

        Args:
            provider_name: If given, only sync this provider. Otherwise sync all enabled.

        Returns:
            The completed SyncJob record.
        """
        job = SyncJob(
            sync_type="library",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        models_discovered = 0
        models_added = 0
        models_updated = 0

        try:
            # Sync Ollama models from unified catalog
            try:
                from backend.app.services.ollama_catalog import get_ollama_catalog

                ollama_models, _source_status = await get_ollama_catalog(force_refresh=True)
                for model in ollama_models:
                    model_info = ProviderModelInfo(
                        provider_model_id=model.get("name", ""),
                        display_name=model.get("name", "").split(":")[0].replace("-", " ").title(),
                        family=model.get("family"),
                        parameter_count=self._parse_param_count(model.get("parameter_size")),
                        context_length=4096,
                        capabilities=model.get("capabilities", []),
                        description=model.get("description", ""),
                        tags=[model.get("family", "")] if model.get("family") else [],
                    )
                    updated = await self._upsert_model(model_info, "ollama")
                    if updated:
                        models_updated += 1
                    else:
                        models_added += 1
                    models_discovered += 1
            except Exception as e:
                logger.warning("ollama_catalog_sync_failed", error=str(e))

            # Sync other registered providers
            if provider_name and provider_name != "ollama":
                adapter = provider_registry.get(provider_name)
                adapters = [adapter] if adapter else []
            elif provider_name is None:
                adapters = [a for a in provider_registry.enabled() if a.name != "ollama"]
            else:
                adapters = []

            for adapter in adapters:
                try:
                    models = await adapter.list_models()
                    models_discovered += len(models)

                    for model_info in models:
                        updated = await self._upsert_model(model_info, adapter.name)
                        if updated:
                            models_updated += 1
                        else:
                            models_added += 1

                    # Link sync job to the first provider found in DB
                    if job.provider_id is None:
                        db_provider = self.db.scalars(select(Provider).where(Provider.name == adapter.name)).first()
                        if db_provider:
                            job.provider_id = db_provider.id

                except Exception as e:
                    logger.error(
                        "sync_provider_failed",
                        provider=adapter.name,
                        error=str(e),
                    )

            self.db.commit()

            job.models_discovered = models_discovered
            job.models_added = models_added
            job.models_updated = models_updated
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)
            logger.error("sync_library_failed", error=str(e))

        return job

    @staticmethod
    def _parse_param_count(param_str: str | None) -> float | None:
        """Parse parameter count string like '7B', '137M' to float in billions."""
        if not param_str:
            return None
        param_str = param_str.strip().upper()
        try:
            if param_str.endswith("B"):
                return float(param_str[:-1])
            elif param_str.endswith("M"):
                return float(param_str[:-1]) / 1000.0
            else:
                return float(param_str)
        except (ValueError, IndexError):
            return None

    async def _upsert_model(self, model_info: ProviderModelInfo, provider_name: str) -> bool:
        """Insert or update a ModelCatalog entry from provider model info.

        Returns True if an existing record was updated, False if created.
        """
        existing = self.db.scalars(
            select(ModelCatalog).where(ModelCatalog.model_id == model_info.provider_model_id)
        ).first()

        now = datetime.now(timezone.utc)

        if existing:
            existing.display_name = model_info.display_name
            existing.family = model_info.family or existing.family
            existing.parameter_count = model_info.parameter_count or existing.parameter_count
            existing.architecture = model_info.architecture or existing.architecture
            existing.context_length_default = model_info.context_length or existing.context_length_default
            existing.capabilities = model_info.capabilities or existing.capabilities
            existing.license = model_info.license or existing.license
            existing.description = model_info.description or existing.description
            existing.tags = model_info.tags or existing.tags
            existing.source_url = model_info.source_url or existing.source_url
            existing.last_updated = now
            return True

        catalog_entry = ModelCatalog(
            model_id=model_info.provider_model_id,
            display_name=model_info.display_name,
            family=model_info.family or "unknown",
            provider=provider_name,
            parameter_count=model_info.parameter_count,
            architecture=model_info.architecture,
            context_length_default=model_info.context_length,
            capabilities=model_info.capabilities or [],
            license=model_info.license,
            description=model_info.description or "",
            tags=model_info.tags or [],
            source_url=model_info.source_url,
            last_updated=now,
        )
        self.db.add(catalog_entry)
        return False

    def get_sync_status(self) -> list[dict]:
        """Return the last 10 sync jobs."""
        jobs = self.db.scalars(select(SyncJob).order_by(SyncJob.created_at.desc()).limit(10)).all()

        return [
            {
                "id": job.id,
                "sync_type": job.sync_type,
                "status": job.status,
                "models_discovered": job.models_discovered,
                "models_added": job.models_added,
                "models_updated": job.models_updated,
                "error_message": job.error_message,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            }
            for job in jobs
        ]
