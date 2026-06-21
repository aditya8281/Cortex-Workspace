"""Base provider adapter interface.

All model providers (Ollama, HuggingFace, LM Studio, OpenRouter) must implement
this interface to integrate with the Model Intelligence System.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderModelInfo:
    """Normalized model information from any provider."""

    provider_model_id: str
    display_name: str
    family: str = ""
    parameter_count: float | None = None
    architecture: str | None = None
    context_length: int | None = None
    capabilities: list[str] = field(default_factory=list)
    license: str | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source_url: str | None = None
    size_bytes: int | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderVariantInfo:
    """Normalized variant/quantization information."""

    variant_id: str
    quantization: str
    size_bytes: int | None = None
    size_gb: float | None = None
    vram_required_gb: float | None = None
    ram_required_gb: float | None = None
    quantization_bits: float | None = None
    download_url: str | None = None
    file_hash: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderDownloadResult:
    """Result of a download operation."""

    success: bool
    file_path: str | None = None
    file_size_bytes: int | None = None
    checksum: str | None = None
    error_message: str | None = None
    model_name: str | None = None  # local model name after install


class ProviderAdapter(ABC):
    """Abstract base class for model providers.

    Each provider (Ollama, HuggingFace, LM Studio, etc.) must implement
    these methods to integrate with the discovery, recommendation, and
    download systems.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g., 'ollama', 'huggingface')."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is reachable and healthy."""

    @abstractmethod
    async def list_models(self) -> list[ProviderModelInfo]:
        """List all available models from this provider."""

    @abstractmethod
    async def get_model_variants(self, model_id: str) -> list[ProviderVariantInfo]:
        """Get all quantization variants for a specific model."""

    @abstractmethod
    async def get_model_detail(self, model_id: str) -> ProviderModelInfo | None:
        """Get detailed information about a specific model."""

    @abstractmethod
    async def download_model(
        self,
        model_id: str,
        variant_id: str | None = None,
        on_progress: callable | None = None,
    ) -> ProviderDownloadResult:
        """Download a model. Calls on_progress(progress_float) during download."""

    @abstractmethod
    async def cancel_download(self, model_id: str) -> bool:
        """Cancel an in-progress download. Returns True if successful."""

    @abstractmethod
    async def delete_model(self, model_id: str) -> bool:
        """Delete a locally installed model."""

    @abstractmethod
    async def list_installed(self) -> list[ProviderModelInfo]:
        """List models installed locally via this provider."""
