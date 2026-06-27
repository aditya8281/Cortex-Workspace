"""Quantization database service — VRAM estimation and quantization info."""

from __future__ import annotations

from typing import cast

import structlog
from sqlalchemy.orm import Session

from backend.app.models.intelligence.model_catalog import Quantization

logger = structlog.get_logger()

# Static fallback data (used if DB not seeded)
QUANT_DATA = {
    "F32": {"bits": 32.0, "quality": 100.0, "speed": 0.5, "memory": 4.0},
    "F16": {"bits": 16.0, "quality": 99.5, "speed": 0.8, "memory": 2.0},
    "BF16": {"bits": 16.0, "quality": 99.5, "speed": 0.8, "memory": 2.0},
    "Q8_0": {"bits": 8.0, "quality": 97.0, "speed": 1.0, "memory": 1.0},
    "Q6_K": {"bits": 6.0, "quality": 95.0, "speed": 1.1, "memory": 0.75},
    "Q5_K_M": {"bits": 5.0, "quality": 93.0, "speed": 1.2, "memory": 0.65},
    "Q5_K_S": {"bits": 5.0, "quality": 92.0, "speed": 1.25, "memory": 0.62},
    "Q4_K_M": {"bits": 4.0, "quality": 90.0, "speed": 1.3, "memory": 0.56},
    "Q4_K_S": {"bits": 4.0, "quality": 88.0, "speed": 1.35, "memory": 0.53},
    "Q4_0": {"bits": 4.0, "quality": 85.0, "speed": 1.3, "memory": 0.5},
    "Q3_K_M": {"bits": 3.0, "quality": 82.0, "speed": 1.4, "memory": 0.44},
    "Q3_K_S": {"bits": 3.0, "quality": 80.0, "speed": 1.45, "memory": 0.41},
    "Q2_K": {"bits": 2.0, "quality": 75.0, "speed": 1.5, "memory": 0.34},
    "IQ4_XS": {"bits": 4.0, "quality": 89.0, "speed": 1.25, "memory": 0.55},
    "IQ3_XXS": {"bits": 3.0, "quality": 81.0, "speed": 1.35, "memory": 0.43},
    "IQ2_XS": {"bits": 2.0, "quality": 73.0, "speed": 1.45, "memory": 0.33},
}


class QuantizationService:
    """Service for quantization lookups and VRAM estimation."""

    def __init__(self, db: Session | None = None):
        self._db = db
        self._cache: dict[str, dict] = {}

    def get_quant_info(self, quantization: str) -> dict | None:
        """Get quantization info by name."""
        name = quantization.upper()
        if name in self._cache:
            return self._cache[name]

        # Try DB first
        if self._db:
            q = self._db.query(Quantization).filter(Quantization.name == name).first()
            if q:
                info = {
                    "name": q.name,
                    "bits_per_param": q.bits_per_param,
                    "quality_score": q.quality_score,
                    "speed_multiplier": q.speed_multiplier,
                    "memory_multiplier": q.memory_multiplier,
                }
                self._cache[name] = info
                return info

        # Fallback to static data
        raw = QUANT_DATA.get(name)
        if raw:
            info = {
                "name": name,
                "bits_per_param": raw["bits"],
                "quality_score": raw["quality"],
                "speed_multiplier": raw["speed"],
                "memory_multiplier": raw["memory"],
            }
            self._cache[name] = info
            return info
        return None

    def estimate_vram_gb(self, parameter_count: float, quantization: str, context_length: int = 4096) -> float:
        """Estimate VRAM requirement in GB."""
        info = self.get_quant_info(quantization)
        bytes_per_param = 0.56 if not info else info["bits_per_param"] / 8.0

        model_size_gb = parameter_count * bytes_per_param

        # KV cache estimation: 2 * n_layers * n_heads * head_dim * context_len * bytes_per_element
        # Rough approximation: 0.5-2GB depending on context length
        kv_cache_gb = max(0.2, context_length / 32768 * 1.0)

        # Framework overhead
        overhead = 0.3

        return model_size_gb + kv_cache_gb + overhead

    def estimate_tps(self, parameter_count: float, quantization: str, bandwidth_gbps: float) -> float | None:
        """Estimate tokens per second based on model size and GPU bandwidth."""
        info = self.get_quant_info(quantization)
        memory_mult = 0.56 if not info else info["memory_multiplier"]

        model_size_gb = parameter_count * memory_mult
        if model_size_gb <= 0 or bandwidth_gbps <= 0:
            return None

        tps = bandwidth_gbps / (2 * model_size_gb)
        return min(tps, 200.0)

    def recommend_quantization(
        self,
        parameter_count: float,
        vram_available_gb: float,
        quality_priority: float = 0.5,
    ) -> list[dict]:
        """Recommend quantizations that fit in available VRAM, sorted by quality.

        Args:
            parameter_count: Model parameter count in billions
            vram_available_gb: Available VRAM in GB
            quality_priority: 0.0 = smallest size, 1.0 = highest quality
        """
        recommendations = []
        for name, data in QUANT_DATA.items():
            vram = self.estimate_vram_gb(parameter_count, name)
            if vram <= vram_available_gb:
                score = data["quality"] * quality_priority + (1.0 - vram / vram_available_gb) * 100 * (
                    1 - quality_priority
                )
                recommendations.append(
                    {
                        "quantization": name,
                        "vram_required_gb": round(vram, 2),
                        "quality_score": data["quality"],
                        "score": round(score, 1),
                    }
                )
        recommendations.sort(key=lambda x: x["score"], reverse=True)  # type: ignore[return-value, arg-type]
        return cast(list[dict], recommendations)
