"""Background sync service for the model catalog.

Discovers models from registered providers and upserts them into ModelCatalog.
"""

from __future__ import annotations

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

        Args:
            provider_name: If given, only sync this provider. Otherwise sync all enabled.

        Returns:
            The completed SyncJob record.
        """
        job = SyncJob(
            sync_type="library",
            status="running",
            started_at=None,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        models_discovered = 0
        models_added = 0

        try:
            if provider_name:
                adapter = provider_registry.get(provider_name)
                adapters = [adapter] if adapter else []
            else:
                adapters = provider_registry.enabled()

            for adapter in adapters:
                try:
                    models = await adapter.list_models()
                    models_discovered += len(models)

                    for model_info in models:
                        added = await self._upsert_model(model_info, adapter.name)
                        if added:
                            models_added += 1

                    # Link sync job to the first provider found in DB
                    if job.provider_id is None:
                        db_provider = self.db.scalars(
                            select(Provider).where(Provider.name == adapter.name)
                        ).first()
                        if db_provider:
                            job.provider_id = db_provider.id

                except Exception as e:
                    logger.error(
                        "sync_provider_failed",
                        provider=adapter.name,
                        error=str(e),
                    )

            job.models_discovered = models_discovered
            job.models_added = models_added
            job.status = "completed"
            self.db.commit()
            self.db.refresh(job)

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            self.db.commit()
            self.db.refresh(job)
            logger.error("sync_library_failed", error=str(e))

        return job

    async def _upsert_model(self, model_info: ProviderModelInfo, provider_name: str) -> bool:
        """Insert or update a ModelCatalog entry from provider model info.

        Returns True if a new record was created, False if updated.
        """
        from datetime import datetime, timezone

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
            self.db.commit()
            self.db.refresh(existing)
            return False

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
        self.db.commit()
        self.db.refresh(catalog_entry)
        return True

    def get_sync_status(self) -> list[dict]:
        """Return the last 10 sync jobs."""
        jobs = self.db.scalars(
            select(SyncJob).order_by(SyncJob.created_at.desc()).limit(10)
        ).all()

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
