"""Intelligence domain models."""

from backend.app.models.intelligence.embedding_cache import EmbeddingCache
from backend.app.models.intelligence.model_catalog import (
    Capability,
    HardwareProfile,
    ModelCatalog,
    ModelDownload,
    ModelStatistics,
    ModelUsage,
    ModelVariant,
    Provider,
    ProviderModel,
    Quantization,
    SyncJob,
)

__all__ = [
    "EmbeddingCache",
    "Capability",
    "HardwareProfile",
    "ModelCatalog",
    "ModelDownload",
    "ModelStatistics",
    "ModelUsage",
    "ModelVariant",
    "Provider",
    "ProviderModel",
    "Quantization",
    "SyncJob",
]
