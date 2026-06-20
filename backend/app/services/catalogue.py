"""Model catalogue management — ingestion, storage, and queries."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.model_catalog import ModelCatalog, ModelVariant

logger = logging.getLogger(__name__)


# Curated model families with metadata
CURATED_FAMILIES: list[dict] = [
    {
        "model_id": "llama-3.1-8b-instruct",
        "family": "llama",
        "display_name": "Llama 3.1 8B Instruct",
        "provider": "ollama",
        "parameter_count": 8.0,
        "architecture": "transformer",
        "context_length_default": 128000,
        "context_length_max": 128000,
        "capabilities": ["chat", "code", "reasoning", "tool_use"],
        "license": "llama3.1",
        "recommended_use_cases": ["coding", "agents", "reasoning", "general"],
        "description": "Meta's Llama 3.1 8B — balanced performance, excellent for coding and agents.",
        "tags": ["meta", "llama", "instruct", "popular"],
    },
    {
        "model_id": "llama-3.1-70b-instruct",
        "family": "llama",
        "display_name": "Llama 3.1 70B Instruct",
        "provider": "ollama",
        "parameter_count": 70.0,
        "architecture": "transformer",
        "context_length_default": 128000,
        "context_length_max": 128000,
        "capabilities": ["chat", "code", "reasoning", "tool_use"],
        "license": "llama3.1",
        "recommended_use_cases": ["high_quality", "reasoning", "coding"],
        "description": "Meta's flagship 70B model — top-tier quality for complex tasks.",
        "tags": ["meta", "llama", "instruct", "high_quality"],
    },
    {
        "model_id": "llama-3.2-3b-instruct",
        "family": "llama",
        "display_name": "Llama 3.2 3B Instruct",
        "provider": "ollama",
        "parameter_count": 3.0,
        "architecture": "transformer",
        "context_length_default": 128000,
        "context_length_max": 128000,
        "capabilities": ["chat", "code", "reasoning"],
        "license": "llama3.2",
        "recommended_use_cases": ["lightweight", "chat", "agents"],
        "description": "Fast, lightweight model ideal for chat and quick tasks.",
        "tags": ["meta", "llama", "instruct", "lightweight", "fast"],
    },
    {
        "model_id": "qwen2.5-7b-instruct",
        "family": "qwen",
        "display_name": "Qwen 2.5 7B Instruct",
        "provider": "ollama",
        "parameter_count": 7.0,
        "architecture": "transformer",
        "context_length_default": 32768,
        "context_length_max": 128000,
        "capabilities": ["chat", "code", "reasoning", "tool_use"],
        "license": "apache-2.0",
        "recommended_use_cases": ["coding", "multilingual", "reasoning"],
        "description": "Alibaba's Qwen 2.5 — strong multilingual and coding capabilities.",
        "tags": ["alibaba", "qwen", "instruct", "multilingual"],
    },
    {
        "model_id": "qwen2.5-coder-7b-instruct",
        "family": "qwen",
        "display_name": "Qwen 2.5 Coder 7B Instruct",
        "provider": "ollama",
        "parameter_count": 7.0,
        "architecture": "transformer",
        "context_length_default": 32768,
        "context_length_max": 128000,
        "capabilities": ["code", "reasoning"],
        "license": "apache-2.0",
        "recommended_use_cases": ["coding"],
        "description": "Specialized coding model — excellent code generation across languages.",
        "tags": ["alibaba", "qwen", "coding", "specialized"],
    },
    {
        "model_id": "qwen2.5-coder-32b-instruct",
        "family": "qwen",
        "display_name": "Qwen 2.5 Coder 32B Instruct",
        "provider": "ollama",
        "parameter_count": 32.0,
        "architecture": "transformer",
        "context_length_default": 32768,
        "context_length_max": 128000,
        "capabilities": ["code", "reasoning"],
        "license": "apache-2.0",
        "recommended_use_cases": ["coding", "high_quality"],
        "description": "Large coding model — top-tier code generation quality.",
        "tags": ["alibaba", "qwen", "coding", "high_quality"],
    },
    {
        "model_id": "deepseek-coder-v2-lite-instruct",
        "family": "deepseek",
        "display_name": "DeepSeek Coder V2 Lite",
        "provider": "ollama",
        "parameter_count": 16.0,
        "architecture": "moe",
        "context_length_default": 128000,
        "context_length_max": 128000,
        "capabilities": ["code", "reasoning"],
        "license": "mit",
        "recommended_use_cases": ["coding"],
        "description": "DeepSeek's code model — excellent across 338 programming languages.",
        "tags": ["deepseek", "coding", "moe"],
    },
    {
        "model_id": "deepseek-r1-distill-qwen-7b",
        "family": "deepseek",
        "display_name": "DeepSeek R1 Distill Qwen 7B",
        "provider": "ollama",
        "parameter_count": 7.0,
        "architecture": "transformer",
        "context_length_default": 32768,
        "context_length_max": 65536,
        "capabilities": ["reasoning", "chat", "code"],
        "license": "mit",
        "recommended_use_cases": ["reasoning", "math", "logic"],
        "description": "Distilled reasoning model — strong math and logic capabilities.",
        "tags": ["deepseek", "reasoning", "distilled"],
    },
    {
        "model_id": "deepseek-r1-distill-llama-70b",
        "family": "deepseek",
        "display_name": "DeepSeek R1 Distill Llama 70B",
        "provider": "ollama",
        "parameter_count": 70.0,
        "architecture": "transformer",
        "context_length_default": 32768,
        "context_length_max": 65536,
        "capabilities": ["reasoning", "chat", "code"],
        "license": "mit",
        "recommended_use_cases": ["reasoning", "high_quality"],
        "description": "Large distilled reasoning model — state-of-the-art reasoning quality.",
        "tags": ["deepseek", "reasoning", "high_quality"],
    },
    {
        "model_id": "phi-3.5-mini-instruct",
        "family": "phi",
        "display_name": "Phi 3.5 Mini Instruct",
        "provider": "ollama",
        "parameter_count": 3.8,
        "architecture": "transformer",
        "context_length_default": 128000,
        "context_length_max": 128000,
        "capabilities": ["chat", "reasoning"],
        "license": "mit",
        "recommended_use_cases": ["lightweight", "reasoning", "chat"],
        "description": "Microsoft's efficient reasoning model — capable for its size.",
        "tags": ["microsoft", "phi", "lightweight"],
    },
    {
        "model_id": "gemma-2-9b-it",
        "family": "gemma",
        "display_name": "Gemma 2 9B Instruct",
        "provider": "ollama",
        "parameter_count": 9.0,
        "architecture": "transformer",
        "context_length_default": 8192,
        "context_length_max": 8192,
        "capabilities": ["chat"],
        "license": "gemma",
        "recommended_use_cases": ["chat", "lightweight"],
        "description": "Google's Gemma 2 — efficient and fast.",
        "tags": ["google", "gemma", "lightweight"],
    },
    {
        "model_id": "mistral-7b-instruct-v0.3",
        "family": "mistral",
        "display_name": "Mistral 7B Instruct v0.3",
        "provider": "ollama",
        "parameter_count": 7.0,
        "architecture": "transformer",
        "context_length_default": 32768,
        "context_length_max": 32768,
        "capabilities": ["chat", "reasoning"],
        "license": "apache-2.0",
        "recommended_use_cases": ["chat", "general"],
        "description": "Mistral's efficient 7B — great performance for its size.",
        "tags": ["mistral", "instruct"],
    },
    {
        "model_id": "mixtral-8x7b-instruct",
        "family": "mixtral",
        "display_name": "Mixtral 8x7B Instruct",
        "provider": "ollama",
        "parameter_count": 46.7,
        "architecture": "moe",
        "context_length_default": 32768,
        "context_length_max": 32768,
        "capabilities": ["chat", "reasoning", "code"],
        "license": "apache-2.0",
        "recommended_use_cases": ["general", "reasoning"],
        "description": "Mistral's MoE model — efficient with strong performance.",
        "tags": ["mistral", "moe"],
    },
    {
        "model_id": "nomic-embed-text",
        "family": "nomic",
        "display_name": "Nomic Embed Text",
        "provider": "ollama",
        "parameter_count": 0.137,
        "architecture": "transformer",
        "context_length_default": 8192,
        "context_length_max": 8192,
        "capabilities": ["embedding"],
        "license": "apache-2.0",
        "recommended_use_cases": ["embeddings", "rag", "search"],
        "description": "High-quality text embeddings for semantic search.",
        "tags": ["nomic", "embedding"],
    },
    {
        "model_id": "llava-llama3-8b",
        "family": "llava",
        "display_name": "LLaVA Llama3 8B",
        "provider": "ollama",
        "parameter_count": 8.0,
        "architecture": "multimodal",
        "context_length_default": 4096,
        "context_length_max": 8192,
        "capabilities": ["chat", "vision"],
        "license": "apache-2.0",
        "recommended_use_cases": ["vision", "image_understanding"],
        "description": "Vision-language model for image understanding.",
        "tags": ["llava", "vision", "multimodal"],
    },
    {
        "model_id": "codellama-7b-instruct",
        "family": "codellama",
        "display_name": "CodeLlama 7B Instruct",
        "provider": "ollama",
        "parameter_count": 7.0,
        "architecture": "transformer",
        "context_length_default": 16384,
        "context_length_max": 100000,
        "capabilities": ["code", "chat"],
        "license": "llama2",
        "recommended_use_cases": ["coding"],
        "description": "Code-specialized Llama model for code generation.",
        "tags": ["meta", "codellama", "coding"],
    },
    {
        "model_id": "starcoder2-7b",
        "family": "starcoder",
        "display_name": "StarCoder2 7B",
        "provider": "ollama",
        "parameter_count": 7.0,
        "architecture": "transformer",
        "context_length_default": 16384,
        "context_length_max": 16384,
        "capabilities": ["code"],
        "license": "bigcode-openrail-m",
        "recommended_use_cases": ["coding", "completion"],
        "description": "Code generation model supporting 619 programming languages.",
        "tags": ["bigcode", "starcoder", "coding"],
    },
]

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
        "F32": 4.0, "F16": 2.0, "Q8_0": 1.0, "Q6_K": 0.75,
        "Q5_K_M": 0.65, "Q5_K_S": 0.62, "Q4_K_M": 0.56, "Q4_K_S": 0.53,
        "Q4_0": 0.5, "Q3_K_M": 0.44, "Q3_K_S": 0.41, "Q2_K": 0.34,
        "IQ4_XS": 0.55, "IQ3_XXS": 0.43, "IQ2_XS": 0.33,
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
        """Seed the catalogue with curated model families."""
        count = 0
        now = datetime.now(timezone.utc)

        for family_data in CURATED_FAMILIES:
            existing = self.db.execute(
                select(ModelCatalog).where(ModelCatalog.model_id == family_data["model_id"])
            ).scalar_one_or_none()

            if existing:
                continue

            catalog = ModelCatalog(
                model_id=family_data["model_id"],
                family=family_data["family"],
                display_name=family_data["display_name"],
                provider=family_data["provider"],
                parameter_count=family_data["parameter_count"],
                architecture=family_data.get("architecture"),
                context_length_default=family_data.get("context_length_default", 4096),
                context_length_max=family_data.get("context_length_max"),
                capabilities=family_data.get("capabilities", ["chat"]),
                license=family_data.get("license"),
                recommended_use_cases=family_data.get("recommended_use_cases", []),
                not_recommended_for=family_data.get("not_recommended_for", []),
                description=family_data.get("description", ""),
                tags=family_data.get("tags", []),
                last_updated=now,
            )
            self.db.add(catalog)
            count += 1

        self.db.commit()
        return count

    def mark_downloaded_models(
        self, installed_ollama_tags: list[str]
    ) -> int:
        """Mark variants as downloaded based on Ollama installed models."""
        updated = 0
        for tag in installed_ollama_tags:
            variant = self.db.execute(
                select(ModelVariant).where(ModelVariant.ollama_tag == tag)
            ).scalar_one_or_none()

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
        return list(
            self.db.execute(
                select(ModelVariant).where(ModelVariant.downloaded)
            ).scalars().all()
        )
