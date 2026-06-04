"""
Model Entity Abstraction Layer

Unified abstraction for all model types (Local, Cloud, Custom)
Ensures clean separation of concerns and provider-agnostic model representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime


class ProviderType(str, Enum):
    """Provider classification"""
    LOCAL = "local"          # Ollama, LM Studio
    CLOUD = "cloud"          # OpenAI, Anthropic, etc.
    CUSTOM = "custom"        # User-defined API endpoints


class ModelSource(str, Enum):
    """Model source identifier"""
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    GROQ = "groq"
    TOGETHER_AI = "together_ai"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    CUSTOM_API = "custom_api"


@dataclass
class ModelEntity:
    """
    Unified model representation.
    
    All models (local, cloud, custom) are abstracted into this entity.
    This ensures consistent handling across the system.
    """
    
    # Identity
    id: str                          # Unique identifier (name or custom ID)
    display_name: str                # Human-readable name
    provider_name: str               # Provider name (Ollama, OpenAI, etc.)
    
    # Classification
    provider_type: ProviderType      # local | cloud | custom
    source: ModelSource              # Specific source (ollama, openai, etc.)
    
    # Model specification
    model_identifier: str            # String used in inference (may differ from display name)
    context_window: int              # Maximum context length
    
    # Metadata
    parameters: Optional[str] = None       # Model size (e.g., "7B", "70B")
    quantization: Optional[str] = None     # Quantization format
    vram_estimate: Optional[str] = None    # Estimated VRAM requirement
    capabilities: Optional[list[str]] = None  # ["coding", "vision", "reasoning"]
    
    # Status
    status: str = "active"           # active | unavailable | downloading
    is_downloaded: bool = False      # Only relevant for local models
    
    # API Details (for cloud/custom models)
    api_endpoint: Optional[str] = None           # API base URL
    api_key_required: bool = False               # Whether API key is needed
    custom_headers: Optional[Dict[str, str]] = None  # Custom headers for API
    
    # Metadata
    is_custom: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.display_name,
            "display_name": self.display_name,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type.value,
            "source": self.source.value,
            "model_identifier": self.model_identifier,
            "context_window": self.context_window,
            "context_length": self.context_window,  # Backward compat
            "parameters": self.parameters,
            "quantization": self.quantization,
            "vram_estimate": self.vram_estimate,
            "capabilities": self.capabilities or [],
            "status": self.status,
            "is_downloaded": self.is_downloaded,
            "is_local": self.provider_type == ProviderType.LOCAL,
            "api_endpoint": self.api_endpoint,
            "api_key_required": self.api_key_required,
            "is_custom": self.is_custom,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelEntity:
        """Create ModelEntity from dictionary"""
        return cls(
            id=data.get("id") or data.get("name"),
            display_name=data.get("display_name") or data.get("name"),
            provider_name=data.get("provider_name"),
            provider_type=ProviderType(data.get("provider_type", "local")),
            source=ModelSource(data.get("source", "ollama")),
            model_identifier=data.get("model_identifier") or data.get("id") or data.get("name"),
            context_window=data.get("context_window") or data.get("context_length", 8192),
            parameters=data.get("parameters"),
            quantization=data.get("quantization"),
            vram_estimate=data.get("vram_estimate"),
            capabilities=data.get("capabilities", []),
            status=data.get("status", "active"),
            is_downloaded=data.get("is_downloaded", False),
            api_endpoint=data.get("api_endpoint"),
            api_key_required=data.get("api_key_required", False),
            custom_headers=data.get("custom_headers"),
            is_custom=data.get("is_custom", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class ModelEntityBuilder:
    """Builder pattern for creating ModelEntity instances"""
    
    @staticmethod
    def from_ollama_model(model_data: Dict[str, Any]) -> ModelEntity:
        """Build from Ollama API response"""
        name = model_data.get("name")
        details = model_data.get("details", {})
        
        return ModelEntity(
            id=name,
            display_name=name,
            provider_name="Ollama",
            provider_type=ProviderType.LOCAL,
            source=ModelSource.OLLAMA,
            model_identifier=name,
            context_window=ModelEntityBuilder._estimate_context(name),
            parameters=details.get("parameter_size", "unknown"),
            quantization=details.get("quantization_level", "unknown"),
            vram_estimate=ModelEntityBuilder._estimate_vram(details.get("parameter_size")),
            status="active",
            is_downloaded=True,
        )
    
    @staticmethod
    def from_cloud_model(model_data: Dict[str, Any], provider_name: str, source: ModelSource) -> ModelEntity:
        """Build from cloud provider API response"""
        model_id = model_data.get("id") or model_data.get("name")
        
        return ModelEntity(
            id=model_id,
            display_name=model_data.get("display_name") or model_id,
            provider_name=provider_name,
            provider_type=ProviderType.CLOUD,
            source=source,
            model_identifier=model_id,
            context_window=model_data.get("context_length", 8192),
            parameters=model_data.get("parameters", "unknown"),
            quantization=model_data.get("quantization", "N/A"),
            vram_estimate=model_data.get("vram_estimate", "N/A"),
            status="active" if model_data.get("active", True) else "unavailable",
            api_key_required=True,
        )
    
    @staticmethod
    def from_custom_model(
        name: str,
        api_endpoint: str,
        model_identifier: str,
        **kwargs
    ) -> ModelEntity:
        """Build custom user-defined model"""
        return ModelEntity(
            id=f"custom_{name.lower().replace(' ', '_')}",
            display_name=name,
            provider_name="Custom",
            provider_type=ProviderType.CUSTOM,
            source=ModelSource.CUSTOM_API,
            model_identifier=model_identifier,
            context_window=kwargs.get("context_window", 8192),
            parameters=kwargs.get("parameters", "unknown"),
            quantization=kwargs.get("quantization", "N/A"),
            vram_estimate="N/A",
            status=kwargs.get("status", "active"),
            api_endpoint=api_endpoint,
            api_key_required=kwargs.get("api_key_required", False),
            custom_headers=kwargs.get("custom_headers"),
            is_custom=True,
        )
    
    @staticmethod
    def _estimate_context(model_name: str) -> int:
        """Estimate context window based on model name"""
        name_lower = model_name.lower()
        
        if "qwen" in name_lower:
            return 32768
        elif "llama3" in name_lower:
            return 8192
        elif "llama2" in name_lower:
            return 4096
        elif "phi" in name_lower:
            return 128000
        elif "mixtral" in name_lower:
            return 32768
        
        return 8192  # Default
    
    @staticmethod
    def _estimate_vram(param_size: Optional[str]) -> str:
        """Estimate VRAM from parameter size"""
        if not param_size:
            return "unknown"
        
        try:
            size_val = float(param_size.replace("B", "").strip())
            # Rough estimate: 1B params ≈ 0.7GB with fp16 quantization
            vram = round(size_val * 0.7, 1)
            return f"{vram} GB"
        except Exception:
            return "unknown"
