"""Model catalogue management — ingestion, storage, and queries."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant

logger = logging.getLogger(__name__)


# Quantization quality mapping
QUANT_QUALITY: dict[str, float] = {
    "F32": 100.0,
    "F16": 99.5,
    "Q8_0": 97.0,
    "Q6_K": 95.0,
    "Q5_K_M": 93.0,
    "Q5_K_S": 92.0,
    "Q4_K_M": 90.0,
    "Q4_K_S": 88.0,
    "Q4_0": 85.0,
    "Q3_K_M": 82.0,
    "Q3_K_S": 80.0,
    "Q2_K": 75.0,
    "IQ4_XS": 89.0,
    "IQ3_XXS": 81.0,
    "IQ2_XS": 73.0,
}


def estimate_vram_gb(parameter_count: float, quantization: str) -> float:
    """Estimate VRAM usage based on parameter count and quantization."""
    quant_bytes = {
        "F32": 4.0,
        "F16": 2.0,
        "Q8_0": 1.0,
        "Q6_K": 0.75,
        "Q5_K_M": 0.65,
        "Q5_K_S": 0.62,
        "Q4_K_M": 0.56,
        "Q4_K_S": 0.53,
        "Q4_0": 0.5,
        "Q3_K_M": 0.44,
        "Q3_K_S": 0.41,
        "Q2_K": 0.34,
        "IQ4_XS": 0.55,
        "IQ3_XXS": 0.43,
        "IQ2_XS": 0.33,
    }
    bytes_per_param = quant_bytes.get(quantization.upper(), 0.56)
    model_gb = parameter_count * bytes_per_param
    overhead = 0.5  # KV cache + framework overhead
    return model_gb + overhead


def estimate_tps_gpu(
    parameter_count: float,
    size_gb: float,
    bandwidth_gbps: float | None,
) -> float | None:
    """Estimate tokens/sec for GPU inference."""
    if not bandwidth_gbps or bandwidth_gbps <= 0:
        return None
    # Rough estimate: TPS ≈ bandwidth / (2 * model_size_in_gb)
    # The "2" accounts for reading weights twice per token (simplified)
    if size_gb <= 0:
        return None
    tps = bandwidth_gbps / (2 * size_gb)
    return min(tps, 200.0)  # Cap at 200 tps


def get_quantization_quality(quantization: str) -> float:
    """Get quality score for a quantization level."""
    return QUANT_QUALITY.get(quantization.upper(), 85.0)


def _quant_level(quantization: str) -> str:
    """Map quantization to level string."""
    q = quantization.upper()
    if q.startswith("F"):
        return "16-bit" if "16" in q else "32-bit"
    if q.startswith("Q8"):
        return "8-bit"
    if q.startswith("Q6"):
        return "6-bit"
    if q.startswith("Q5"):
        return "5-bit"
    if q.startswith("Q4") or q.startswith("IQ4"):
        return "4-bit"
    if q.startswith("Q3") or q.startswith("IQ3"):
        return "3-bit"
    if q.startswith("Q2") or q.startswith("IQ2"):
        return "2-bit"
    return "unknown"


class CatalogueManager:
    """Manages the model catalogue — ingestion, storage, queries."""

    def __init__(self, db: Session):
        self.db = db

    def seed_curated_models(self) -> int:
        """Seed the catalogue with models from the unified catalog.

        Backward-compatible wrapper around ingest_from_catalog().
        """
        return self.ingest_from_catalog()

    @staticmethod
    def _compute_recommended_use_cases(capabilities: list) -> list[str]:
        """Auto-assign recommended_use_cases based on capabilities."""
        if "embedding" in capabilities:
            return ["semantic search", "RAG", "text embeddings"]
        if "code" in capabilities:
            return ["code generation", "programming assistance"]
        if "vision" in capabilities:
            return ["image understanding", "visual Q&A"]
        if not capabilities or "chat" in capabilities:
            return ["general chat", "Q&A"]
        return ["general chat", "Q&A"]

    def ingest_from_catalog(self, force_refresh: bool = False) -> int:
        """Ingest models from the unified Ollama catalog into the database.

        Uses the three-source pipeline (OCI Registry, Cloud API, Local API)
        instead of hardcoded model families.
        """
        try:
            from backend.app.services.intelligence.ollama_catalog import get_ollama_catalog_sync

            models, _source_status = get_ollama_catalog_sync(force_refresh=force_refresh)
        except Exception as e:
            logger.warning("Failed to fetch catalog: %s", e)
            return 0

        count = 0
        now = datetime.now(timezone.utc)

        for model in models:
            name = model.get("name", "")
            base_name = name.split(":")[0]
            tag = name.split(":")[1] if ":" in name else "latest"

            # Extract metadata from catalog entry
            family = model.get("family", "") or base_name
            param_size = model.get("parameter_size", "")
            capabilities = model.get("capabilities", [])
            model.get("source", "registry")

            # Try to parse parameter count
            param_count = self._parse_param_count(param_size)

            # Create/update catalog entry (one per base model)
            existing = self.db.execute(
                select(ModelCatalog).where(ModelCatalog.model_id == base_name)
            ).scalar_one_or_none()

            if existing:
                # Update capabilities if we have better data from new source
                if capabilities and not existing.capabilities:
                    existing.capabilities = capabilities
                # Pipe enrichment fields that were previously ignored
                existing.license = model.get("license") or existing.license
                if model.get("context_length"):
                    existing.context_length_default = model["context_length"]
                existing.architecture = model.get("architecture") or existing.architecture
                existing.embedding_dim = model.get("embedding_dim") or existing.embedding_dim
                existing.pooling_type = model.get("pooling_type") or existing.pooling_type
                existing.recommended_use_cases = self._compute_recommended_use_cases(
                    model.get("capabilities", existing.capabilities or [])
                )
                existing.last_updated = now
                catalog_id = existing.id
            else:
                catalog = ModelCatalog(
                    model_id=base_name,
                    family=family,
                    display_name=base_name.replace("-", " ").title(),
                    provider="ollama",
                    parameter_count=param_count,
                    context_length_default=model.get("context_length", 4096),
                    capabilities=capabilities or ["chat"],
                    description=model.get("description", f"Ollama model: {base_name}"),
                    tags=[family] if family else [],
                    last_updated=now,
                    # Pipe enrichment fields that were previously ignored
                    license=model.get("license"),
                    architecture=model.get("architecture"),
                    embedding_dim=model.get("embedding_dim"),
                    pooling_type=model.get("pooling_type"),
                    recommended_use_cases=self._compute_recommended_use_cases(
                        capabilities or ["chat"]
                    ),
                )
                self.db.add(catalog)
                self.db.flush()
                catalog_id = catalog.id
                count += 1

            # Create/update variant entry
            variant_id = f"{base_name}:{tag}"
            existing_variant = self.db.execute(
                select(ModelVariant).where(ModelVariant.variant_id == variant_id)
            ).scalar_one_or_none()

            if not existing_variant:
                size_bytes = model.get("size", 0) or model.get("size_bytes", 0)
                quantization = model.get("quantization", "")
                vram = estimate_vram_gb(param_count or 7.0, quantization) if param_count else None

                variant = ModelVariant(
                    model_catalog_id=catalog_id,
                    variant_id=variant_id,
                    quantization=quantization.upper() if quantization else "UNKNOWN",
                    quantization_level=_quant_level(quantization) if quantization else "unknown",
                    parameter_count=param_count,
                    size_bytes=size_bytes,
                    size_gb=size_bytes / (1024**3) if size_bytes else 0,
                    vram_required_gb=vram,
                    ram_required_gb=(vram * 1.2) if vram else None,
                    recommended_vram_gb=(vram * 1.3) if vram else None,
                    quality_score=get_quantization_quality(quantization) if quantization else 85.0,
                    ollama_tag=variant_id,
                    downloaded=False,
                )
                self.db.add(variant)

        self.db.commit()
        return count

    @staticmethod
    def _parse_param_count(param_str: str | None) -> float | None:
        """Parse parameter count string like '7B', '8B', '137M' to float in billions."""
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

    def mark_downloaded_models(self, installed_ollama_tags: list[str]) -> int:
        """Mark variants as downloaded based on Ollama installed models."""
        updated = 0
        for tag in installed_ollama_tags:
            variant = self.db.execute(select(ModelVariant).where(ModelVariant.ollama_tag == tag)).scalar_one_or_none()

            if variant and not variant.downloaded:
                variant.downloaded = True
                variant.last_downloaded_at = datetime.now(timezone.utc)
                updated += 1

        self.db.commit()
        return updated

    def upsert_variant(
        self,
        model_catalog_id: int,
        variant_id: str,
        quantization: str,
        size_bytes: int,
        ollama_tag: str | None = None,
        huggingface_repo: str | None = None,
        huggingface_file: str | None = None,
    ) -> ModelVariant:
        """Insert or update a model variant."""
        existing = self.db.execute(
            select(ModelVariant).where(ModelVariant.variant_id == variant_id)
        ).scalar_one_or_none()

        # Get parent model info for estimation
        catalog = self.db.get(ModelCatalog, model_catalog_id)
        param_count = catalog.parameter_count if catalog else None

        # Estimate hardware requirements
        vram = estimate_vram_gb(param_count or 7.0, quantization) if param_count else None
        ram = (vram * 1.2) if vram else None
        quality = get_quantization_quality(quantization)
        size_gb = size_bytes / (1024**3) if size_bytes else 0

        if existing:
            existing.size_bytes = size_bytes
            existing.size_gb = size_gb
            existing.vram_required_gb = vram
            existing.ram_required_gb = ram
            existing.quality_score = quality
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return existing

        variant = ModelVariant(
            model_catalog_id=model_catalog_id,
            variant_id=variant_id,
            quantization=quantization.upper(),
            quantization_level=_quant_level(quantization),
            parameter_count=param_count,
            size_bytes=size_bytes,
            size_gb=size_gb,
            vram_required_gb=vram,
            ram_required_gb=ram,
            recommended_vram_gb=(vram * 1.3) if vram else None,
            quality_score=quality,
            ollama_tag=ollama_tag,
            huggingface_repo=huggingface_repo,
            huggingface_file=huggingface_file,
            downloaded=False,
        )
        self.db.add(variant)
        self.db.commit()
        return variant

    def get_all_catalogue(self) -> list[ModelCatalog]:
        """Get all catalogue entries."""
        return list(self.db.execute(select(ModelCatalog)).scalars().all())

    def get_downloaded_variants(self) -> list[ModelVariant]:
        """Get all downloaded model variants."""
        return list(self.db.execute(select(ModelVariant).where(ModelVariant.downloaded)).scalars().all())
