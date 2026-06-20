"""Hardware-aware recommendation engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.app.models.model_catalog import ModelCatalog, ModelVariant
from backend.app.services.catalogue import (
    estimate_tps_gpu,
    estimate_vram_gb,
    get_quantization_quality,
)
from backend.app.services.hardware import HardwareProfile

logger = logging.getLogger(__name__)

# Workload definitions
WORKLOADS = {
    "coding": {
        "label": "Coding",
        "description": "Code generation, completion, review",
        "preferred_families": ["deepseek", "qwen", "codellama", "starcoder", "llama"],
        "preferred_capabilities": ["code"],
        "min_parameter_count": 3.0,
        "priority_families": ["deepseek", "qwen", "codellama"],
    },
    "reasoning": {
        "label": "Reasoning",
        "description": "Complex reasoning, math, logic",
        "preferred_families": ["deepseek", "phi", "qwen", "llama"],
        "preferred_capabilities": ["reasoning"],
        "min_parameter_count": 3.0,
        "priority_families": ["deepseek", "phi"],
    },
    "agents": {
        "label": "Agents & Tool Use",
        "description": "Function calling, tool orchestration",
        "preferred_families": ["llama", "qwen", "mistral"],
        "preferred_capabilities": ["tool_use", "chat"],
        "min_parameter_count": 3.0,
        "priority_families": ["llama", "qwen"],
    },
    "vision": {
        "label": "Vision",
        "description": "Image understanding, OCR, VQA",
        "preferred_families": ["llava"],
        "preferred_capabilities": ["vision"],
        "min_parameter_count": 3.0,
        "priority_families": ["llava"],
    },
    "embeddings": {
        "label": "Embeddings",
        "description": "Vector embeddings for RAG/search",
        "preferred_families": ["nomic", "bge", "mxbai"],
        "preferred_capabilities": ["embedding"],
        "min_parameter_count": 0.0,
        "priority_families": ["nomic", "bge"],
    },
    "lightweight": {
        "label": "Lightweight & Fast",
        "description": "Fast responses, low resource use",
        "preferred_families": ["phi", "qwen", "llama", "gemma"],
        "preferred_capabilities": ["chat"],
        "min_parameter_count": 0.0,
        "max_parameter_count": 4.0,
        "priority_families": ["phi", "qwen"],
    },
    "high_quality": {
        "label": "High Quality",
        "description": "Best quality regardless of speed",
        "preferred_families": ["llama", "qwen", "deepseek"],
        "preferred_capabilities": [],
        "min_parameter_count": 30.0,
        "priority_families": ["llama", "qwen", "deepseek"],
    },
    "rag": {
        "label": "RAG",
        "description": "Retrieval-augmented generation",
        "preferred_families": ["llama", "qwen"],
        "preferred_capabilities": ["chat", "reasoning"],
        "min_parameter_count": 3.0,
        "context_length_min": 16384,
        "priority_families": ["llama", "qwen"],
    },
}


@dataclass
class PerformanceEstimate:
    """Estimated performance for a model on current hardware."""
    tokens_per_second: float | None = None
    prompt_eval_tps: float | None = None
    memory_usage_gb: float = 0.0
    vram_usage_gb: float = 0.0
    ram_usage_gb: float = 0.0
    quantization_quality: str = "unknown"
    quality_notes: str = ""
    backend_recommendation: str = "auto"
    gpu_offload_layers: int | None = None
    context_length_max: int = 4096
    speed_rating: str = "unknown"
    fit_rating: str = "unknown"  # "excellent", "good", "usable", "too_large"


@dataclass
class ModelRecommendation:
    """A single model recommendation."""
    catalog_entry: ModelCatalog
    variant: ModelVariant | None = None
    score: float = 0.0
    performance: PerformanceEstimate = field(default_factory=PerformanceEstimate)
    explanation: str = ""
    why_recommended: str = ""
    quality_tradeoff: str = ""
    hardware_suitability: str = ""


class RecommendationEngine:
    """Generates hardware-aware model recommendations."""

    def __init__(self, hardware: HardwareProfile):
        self.hardware = hardware

    def recommend_for_workload(
        self,
        workload: str,
        models: list[ModelCatalog],
        max_results: int = 5,
    ) -> list[ModelRecommendation]:
        """Get top recommendations for a specific workload."""
        workload_config = WORKLOADS.get(workload, WORKLOADS.get("coding", {}))
        candidates = self._filter_candidates(models, workload_config)

        recommendations = []
        for model in candidates:
            rec = self._evaluate_model(model, workload_config)
            if rec:
                recommendations.append(rec)

        # Sort by score descending
        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:max_results]

    def recommend_all(self, models: list[ModelCatalog]) -> dict[str, list[ModelRecommendation]]:
        """Get recommendations for all workloads."""
        result = {}
        for workload_id in WORKLOADS:
            result[workload_id] = self.recommend_for_workload(workload_id, models)
        return result

    def _filter_candidates(
        self, models: list[ModelCatalog], config: dict
    ) -> list[ModelCatalog]:
        """Filter models to candidates for a workload."""
        candidates = []
        preferred_families = config.get("preferred_families", [])
        preferred_caps = config.get("preferred_capabilities", [])
        min_params = config.get("min_parameter_count", 0)
        max_params = config.get("max_parameter_count")
        min_ctx = config.get("context_length_min", 0)

        for model in models:
            # Filter by parameter count
            if model.parameter_count is not None:
                if model.parameter_count < min_params:
                    continue
                if max_params and model.parameter_count > max_params:
                    continue

            # Filter by context length
            if model.context_length_default and model.context_length_default < min_ctx:
                continue

            # Prefer models matching workload
            if preferred_families:
                if model.family in preferred_families:
                    candidates.append(model)
                elif preferred_caps:
                    model_caps = model.capabilities or []
                    if any(c in model_caps for c in preferred_caps):
                        candidates.append(model)
            else:
                candidates.append(model)

        return candidates

    def _evaluate_model(
        self, model: ModelCatalog, config: dict
    ) -> ModelRecommendation | None:
        """Evaluate a model and generate a recommendation."""
        # Find best variant for this hardware
        best_variant = self._find_best_variant(model)
        if not best_variant:
            return None

        # Calculate feasibility score
        score = self._calculate_score(model, best_variant, config)

        # Generate performance estimate
        performance = self._estimate_performance(model, best_variant)

        # Generate explanation
        explanation = self._generate_explanation(model, best_variant, performance, config)

        return ModelRecommendation(
            catalog_entry=model,
            variant=best_variant,
            score=score,
            performance=performance,
            explanation=explanation["why"],
            why_recommended=explanation["why"],
            quality_tradeoff=explanation["tradeoff"],
            hardware_suitability=explanation["suitability"],
        )

    def _find_best_variant(self, model: ModelCatalog) -> ModelVariant | None:
        """Find the best quantization variant for current hardware."""
        # Prefer Q4_K_M as default — good balance of quality and size
        preferred_quants = ["Q4_K_M", "Q5_K_M", "Q8_0", "Q4_K_S", "Q6_K"]

        for quant in preferred_quants:
            param_count = model.parameter_count or 7.0
            vram_needed = estimate_vram_gb(param_count, quant)

            # Check if it fits
            if self.hardware.gpu_available and self.hardware.vram_total_gb > 0:
                if vram_needed <= self.hardware.vram_available_gb:
                    return self._make_virtual_variant(model, quant, vram_needed)
            else:
                # CPU-only: check RAM
                ram_needed = vram_needed * 1.2
                if ram_needed <= self.hardware.ram_available_gb:
                    return self._make_virtual_variant(model, quant, vram_needed)

        # Fallback: smallest quantization
        param_count = model.parameter_count or 7.0
        return self._make_virtual_variant(model, "Q4_K_M", estimate_vram_gb(param_count, "Q4_K_M"))

    def _make_virtual_variant(
        self, model: ModelCatalog, quantization: str, vram_gb: float
    ) -> ModelVariant:
        """Create a virtual variant for scoring (not persisted)."""
        param_count = model.parameter_count or 7.0
        size_bytes = int(
            param_count
            * {"Q4_K_M": 0.56, "Q5_K_M": 0.65, "Q8_0": 1.0, "Q4_K_S": 0.53, "Q6_K": 0.75}.get(
                quantization, 0.56
            )
            * (1024**3)
        )

        variant = ModelVariant(
            model_catalog_id=0,
            variant_id=f"{model.model_id}:{quantization.lower()}",
            quantization=quantization,
            parameter_count=param_count,
            size_bytes=size_bytes,
            size_gb=size_bytes / (1024**3),
            vram_required_gb=vram_gb,
            ram_required_gb=vram_gb * 1.2,
            recommended_vram_gb=vram_gb * 1.3,
            quality_score=get_quantization_quality(quantization),
            downloaded=False,
        )
        return variant

    def _calculate_score(
        self, model: ModelCatalog, variant: ModelVariant, config: dict
    ) -> float:
        """Calculate feasibility score (0-100)."""
        score = 50.0  # Base score

        # VRAM fit (30 points)
        if self.hardware.gpu_available and self.hardware.vram_total_gb > 0:
            vram_needed = variant.vram_required_gb or 0
            vram_available = self.hardware.vram_available_gb
            if vram_needed <= vram_available * 0.8:
                score += 30  # Excellent fit
            elif vram_needed <= vram_available:
                score += 20  # Good fit
            elif vram_needed <= vram_available * 1.2:
                score += 10  # Tight fit
            else:
                score -= 20  # Doesn't fit well
        else:
            # CPU-only: check RAM
            ram_needed = variant.ram_required_gb or 0
            if ram_needed <= self.hardware.ram_available_gb * 0.8:
                score += 20
            elif ram_needed <= self.hardware.ram_available_gb:
                score += 10
            else:
                score -= 20

        # Quantization quality (20 points)
        quality = variant.quality_score or 85.0
        score += (quality / 100.0) * 20

        # Expected TPS (20 points)
        bandwidth = self.hardware.gpu_memory_bandwidth_gbps
        tps = estimate_tps_gpu(
            variant.parameter_count or 7.0,
            variant.size_gb or 4.0,
            bandwidth,
        )
        if tps:
            if tps > 40:
                score += 20
            elif tps > 20:
                score += 15
            elif tps > 10:
                score += 10
            else:
                score += 5

        # Workload match (15 points)
        priority_families = config.get("priority_families", [])
        if model.family in priority_families:
            score += 15
        elif model.family in config.get("preferred_families", []):
            score += 8

        # Disk space (5 points)
        size_gb = variant.size_gb or 4.0
        if size_gb <= self.hardware.disk_free_gb * 0.5:
            score += 5
        elif size_gb <= self.hardware.disk_free_gb:
            score += 2
        else:
            score -= 10

        return max(0, min(100, score))

    def _estimate_performance(
        self, model: ModelCatalog, variant: ModelVariant
    ) -> PerformanceEstimate:
        """Estimate performance for a model variant."""
        bandwidth = self.hardware.gpu_memory_bandwidth_gbps
        param_count = variant.parameter_count or 7.0
        size_gb = variant.size_gb or 4.0

        # GPU TPS
        gpu_tps = estimate_tps_gpu(param_count, size_gb, bandwidth)

        # CPU TPS (rough: 0.5-2 tps per core for 7B model)
        cpu_tps = min(
            self.hardware.cpu_threads * 0.8,
            20.0 if param_count <= 3 else 10.0 if param_count <= 8 else 3.0,
        )

        # Memory usage
        vram_needed = variant.vram_required_gb or 0
        ram_needed = variant.ram_required_gb or 0

        # Context length that fits
        kv_cache_per_1k_ctx = param_count * 0.001  # Rough: 1MB per 1K context per B params
        if self.hardware.gpu_available and self.hardware.vram_total_gb > 0:
            remaining_vram = self.hardware.vram_available_gb - vram_needed
            max_ctx = (
                int((remaining_vram / kv_cache_per_1k_ctx) * 1000)
                if kv_cache_per_1k_ctx > 0
                else 4096
            )
        else:
            remaining_ram = self.hardware.ram_available_gb - ram_needed
            max_ctx = (
                int((remaining_ram / kv_cache_per_1k_ctx) * 1000)
                if kv_cache_per_1k_ctx > 0
                else 4096
            )

        max_ctx = max(1024, min(max_ctx, model.context_length_max or 128000))

        # Speed rating
        effective_tps = gpu_tps if gpu_tps else cpu_tps
        if effective_tps and effective_tps > 40:
            speed_rating = "fast"
        elif effective_tps and effective_tps > 20:
            speed_rating = "good"
        elif effective_tps and effective_tps > 10:
            speed_rating = "usable"
        else:
            speed_rating = "slow"

        # Fit rating
        total_needed = vram_needed if self.hardware.gpu_available else ram_needed
        total_available = (
            self.hardware.vram_available_gb
            if self.hardware.gpu_available
            else self.hardware.ram_available_gb
        )
        if total_needed <= total_available * 0.6:
            fit_rating = "excellent"
        elif total_needed <= total_available * 0.85:
            fit_rating = "good"
        elif total_needed <= total_available:
            fit_rating = "usable"
        else:
            fit_rating = "too_large"

        # Quantization quality
        quality = variant.quality_score or 85.0
        if quality >= 95:
            quant_quality = "near-lossless"
            quality_notes = "Virtually identical to full precision."
        elif quality >= 90:
            quant_quality = "excellent"
            quality_notes = "Barely noticeable quality loss (~1-2%)."
        elif quality >= 85:
            quant_quality = "good"
            quality_notes = "Minor quality loss (~3-5%). Good for most tasks."
        elif quality >= 80:
            quant_quality = "acceptable"
            quality_notes = "Noticeable quality loss (~5-10%). Usable for chat/code."
        else:
            quant_quality = "degraded"
            quality_notes = "Significant quality loss. Use only if hardware-limited."

        return PerformanceEstimate(
            tokens_per_second=gpu_tps or cpu_tps,
            prompt_eval_tps=gpu_tps * 2 if gpu_tps else cpu_tps * 1.5,
            memory_usage_gb=total_needed,
            vram_usage_gb=vram_needed,
            ram_usage_gb=ram_needed,
            quantization_quality=quant_quality,
            quality_notes=quality_notes,
            backend_recommendation="ollama",
            context_length_max=max_ctx,
            speed_rating=speed_rating,
            fit_rating=fit_rating,
        )

    def _generate_explanation(
        self,
        model: ModelCatalog,
        variant: ModelVariant,
        performance: PerformanceEstimate,
        config: dict,
    ) -> dict:
        """Generate human-readable explanation for a recommendation."""
        hw = self.hardware
        quant = variant.quantization
        tps = performance.tokens_per_second

        # Why recommended
        why_parts = []
        if performance.fit_rating in ("excellent", "good"):
            if hw.gpu_available:
                fit_word = "comfortably" if performance.fit_rating == "excellent" else "well"
                why_parts.append(f"Fits {fit_word} in your {hw.vram_total_gb:.0f}GB VRAM")
            else:
                why_parts.append(f"Fits in your {hw.ram_total_gb:.0f}GB RAM")
        if tps and tps > 20:
            why_parts.append(f"~{tps:.0f} tokens/sec generation")
        why_parts.append(f"{quant} quantization provides {performance.quantization_quality} quality")

        # Quality tradeoff
        tradeoff = performance.quality_notes
        if quant == "Q4_K_M":
            tradeoff += " Q4_K_M is the recommended default for most use cases."
        elif quant == "Q8_0":
            tradeoff += " Q8_0 is near-identical to the original model."

        # Hardware suitability
        if performance.fit_rating == "excellent":
            suitability = "Excellent fit — runs great on your hardware."
        elif performance.fit_rating == "good":
            suitability = "Good fit — comfortable for everyday use."
        elif performance.fit_rating == "usable":
            suitability = "Usable — may be slow or need reduced context length."
        else:
            suitability = "Exceeds available resources — consider a smaller variant."

        return {
            "why": ". ".join(why_parts) + ".",
            "tradeoff": tradeoff,
            "suitability": suitability,
        }
