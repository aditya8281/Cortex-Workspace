"""Seed data for providers, quantizations, and capabilities."""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.model_catalog import Capability, Provider, Quantization

logger = structlog.get_logger()

PROVIDERS: list[dict] = [
    {
        "name": "ollama",
        "display_name": "Ollama",
        "provider_type": "local",
        "base_url": "http://localhost:11434",
        "api_key_required": False,
        "capabilities": ["chat", "code", "vision", "embedding", "reasoning", "tool_use"],
    },
    {
        "name": "huggingface",
        "display_name": "HuggingFace",
        "provider_type": "registry",
        "base_url": "https://huggingface.co",
        "api_key_required": True,
        "capabilities": ["chat", "code", "vision", "embedding", "reasoning", "tool_use"],
    },
    {
        "name": "lmstudio",
        "display_name": "LM Studio",
        "provider_type": "local",
        "base_url": "http://localhost:1234",
        "api_key_required": False,
        "capabilities": ["chat", "code", "vision", "embedding", "reasoning"],
    },
    {
        "name": "openrouter",
        "display_name": "OpenRouter",
        "provider_type": "api",
        "base_url": "https://openrouter.ai/api",
        "api_key_required": True,
        "capabilities": ["chat", "code", "vision", "embedding", "reasoning", "tool_use", "audio", "multimodal"],
    },
]

QUANTIZATIONS: list[dict] = [
    {
        "name": "F32",
        "display_name": "FP32",
        "bits_per_param": 32.0,
        "quality_score": 100.0,
        "speed_multiplier": 1.0,
        "memory_multiplier": 4.0,
        "description": "Full 32-bit floating point — maximum quality, highest memory usage.",
    },
    {
        "name": "F16",
        "display_name": "FP16",
        "bits_per_param": 16.0,
        "quality_score": 99.5,
        "speed_multiplier": 1.1,
        "memory_multiplier": 2.0,
        "description": "Half-precision floating point — negligible quality loss, half the memory.",
    },
    {
        "name": "BF16",
        "display_name": "BF16",
        "bits_per_param": 16.0,
        "quality_score": 99.5,
        "speed_multiplier": 1.1,
        "memory_multiplier": 2.0,
        "description": "Brain floating point — same size as FP16 with better training stability.",
    },
    {
        "name": "Q8_0",
        "display_name": "Q8_0",
        "bits_per_param": 8.0,
        "quality_score": 97.0,
        "speed_multiplier": 1.2,
        "memory_multiplier": 1.0,
        "description": "8-bit integer quantization — strong quality with significant memory savings.",
    },
    {
        "name": "Q6_K",
        "display_name": "Q6_K",
        "bits_per_param": 6.5,
        "quality_score": 95.0,
        "speed_multiplier": 1.3,
        "memory_multiplier": 0.75,
        "description": "6-bit K-quant — excellent quality-to-size ratio.",
    },
    {
        "name": "Q5_K_M",
        "display_name": "Q5_K_M",
        "bits_per_param": 5.5,
        "quality_score": 93.0,
        "speed_multiplier": 1.4,
        "memory_multiplier": 0.65,
        "description": "5-bit K-quant medium — balanced quality and compression.",
    },
    {
        "name": "Q5_K_S",
        "display_name": "Q5_K_S",
        "bits_per_param": 5.3,
        "quality_score": 92.0,
        "speed_multiplier": 1.4,
        "memory_multiplier": 0.62,
        "description": "5-bit K-quant small — slightly more compression than Q5_K_M.",
    },
    {
        "name": "Q4_K_M",
        "display_name": "Q4_K_M",
        "bits_per_param": 4.8,
        "quality_score": 90.0,
        "speed_multiplier": 1.5,
        "memory_multiplier": 0.56,
        "description": "4-bit K-quant medium — popular choice for local deployment.",
    },
    {
        "name": "Q4_K_S",
        "display_name": "Q4_K_S",
        "bits_per_param": 4.5,
        "quality_score": 88.0,
        "speed_multiplier": 1.5,
        "memory_multiplier": 0.53,
        "description": "4-bit K-quant small — more aggressive compression.",
    },
    {
        "name": "Q4_0",
        "display_name": "Q4_0",
        "bits_per_param": 4.5,
        "quality_score": 85.0,
        "speed_multiplier": 1.5,
        "memory_multiplier": 0.5,
        "description": "4-bit quantization — basic but effective compression.",
    },
    {
        "name": "Q3_K_M",
        "display_name": "Q3_K_M",
        "bits_per_param": 3.9,
        "quality_score": 82.0,
        "speed_multiplier": 1.6,
        "memory_multiplier": 0.44,
        "description": "3-bit K-quant medium — aggressive compression with moderate quality loss.",
    },
    {
        "name": "Q3_K_S",
        "display_name": "Q3_K_S",
        "bits_per_param": 3.5,
        "quality_score": 80.0,
        "speed_multiplier": 1.6,
        "memory_multiplier": 0.41,
        "description": "3-bit K-quant small — high compression, noticeable quality loss.",
    },
    {
        "name": "Q2_K",
        "display_name": "Q2_K",
        "bits_per_param": 3.5,
        "quality_score": 75.0,
        "speed_multiplier": 1.7,
        "memory_multiplier": 0.34,
        "description": "2-bit K-quant — extreme compression, significant quality degradation.",
    },
    {
        "name": "IQ4_XS",
        "display_name": "IQ4_XS",
        "bits_per_param": 4.2,
        "quality_score": 89.0,
        "speed_multiplier": 1.5,
        "memory_multiplier": 0.55,
        "description": "Importance quantization 4-bit — optimized bit allocation per layer.",
    },
    {
        "name": "IQ3_XXS",
        "display_name": "IQ3_XXS",
        "bits_per_param": 3.4,
        "quality_score": 81.0,
        "speed_multiplier": 1.6,
        "memory_multiplier": 0.43,
        "description": "Importance quantization 3-bit — aggressive but smarter than Q3.",
    },
    {
        "name": "IQ2_XS",
        "display_name": "IQ2_XS",
        "bits_per_param": 2.5,
        "quality_score": 73.0,
        "speed_multiplier": 1.7,
        "memory_multiplier": 0.33,
        "description": "Importance quantization 2-bit — ultra-compact with smart bit distribution.",
    },
]

CAPABILITIES: list[dict] = [
    {
        "name": "chat",
        "display_name": "Chat",
        "description": "Conversational text generation and instruction following.",
        "icon": "chat",
    },
    {
        "name": "code",
        "display_name": "Code",
        "description": "Code generation, completion, and explanation across programming languages.",
        "icon": "code",
    },
    {
        "name": "vision",
        "display_name": "Vision",
        "description": "Image understanding, visual question answering, and image description.",
        "icon": "eye",
    },
    {
        "name": "embedding",
        "display_name": "Embedding",
        "description": "Text embedding generation for semantic search and similarity.",
        "icon": "layers",
    },
    {
        "name": "reasoning",
        "display_name": "Reasoning",
        "description": "Logical reasoning, math, and complex problem solving.",
        "icon": "brain",
    },
    {
        "name": "tool_use",
        "display_name": "Tool Use",
        "description": "Function calling and external tool integration.",
        "icon": "wrench",
    },
    {
        "name": "audio",
        "display_name": "Audio",
        "description": "Speech recognition, audio understanding, and audio generation.",
        "icon": "mic",
    },
    {
        "name": "multimodal",
        "display_name": "Multimodal",
        "description": "Multi-modal input/output across text, images, audio, and video.",
        "icon": "sparkles",
    },
]


def seed_providers(db: Session) -> int:
    """Seed providers. Returns number of newly inserted rows."""
    count = 0
    for data in PROVIDERS:
        existing = db.execute(select(Provider).where(Provider.name == data["name"])).scalar_one_or_none()
        if existing:
            continue
        db.add(Provider(**data))
        count += 1
    db.commit()
    logger.info("seed_providers_done", count=count)
    return count


def seed_quantizations(db: Session) -> int:
    """Seed quantizations. Returns number of newly inserted rows."""
    count = 0
    for data in QUANTIZATIONS:
        existing = db.execute(select(Quantization).where(Quantization.name == data["name"])).scalar_one_or_none()
        if existing:
            continue
        db.add(Quantization(**data))
        count += 1
    db.commit()
    logger.info("seed_quantizations_done", count=count)
    return count


def seed_capabilities(db: Session) -> int:
    """Seed capabilities. Returns number of newly inserted rows."""
    count = 0
    for data in CAPABILITIES:
        existing = db.execute(select(Capability).where(Capability.name == data["name"])).scalar_one_or_none()
        if existing:
            continue
        db.add(Capability(**data))
        count += 1
    db.commit()
    logger.info("seed_capabilities_done", count=count)
    return count


def seed_all(db: Session) -> dict[str, int]:
    """Run all seed functions. Returns counts per table."""
    return {
        "providers": seed_providers(db),
        "quantizations": seed_quantizations(db),
        "capabilities": seed_capabilities(db),
    }
