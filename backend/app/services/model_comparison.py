"""Side-by-side model comparison service."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.app.models.model_catalog import ModelCatalog
from backend.app.services.catalogue import estimate_vram_gb, get_quantization_quality
from backend.app.services.hardware import HardwareProfile

logger = logging.getLogger(__name__)

COMPARISON_DIMENSIONS = [
    "parameter_count",
    "context_length",
    "quality",
    "vram_required",
    "speed",
]

MAX_COMPARE = 5
MIN_COMPARE = 2


@dataclass
class DimensionResult:
    """Result for a single comparison dimension."""
    dimension: str
    display_name: str
    values: dict[str, float | str | None] = field(default_factory=dict)
    winner: str | None = None
    higher_is_better: bool = True


@dataclass
class ComparisonResult:
    """Full comparison result for 2-5 models."""
    models: list[str]
    dimensions: list[DimensionResult] = field(default_factory=list)
    winner_model: str | None = None
    dimension_wins: dict[str, int] = field(default_factory=dict)
    summary: str = ""


class ModelComparisonService:
    """Compare multiple models side-by-side across key dimensions."""

    def compare(
        self,
        models: list[ModelCatalog],
        hardware: HardwareProfile | None = None,
    ) -> ComparisonResult:
        """Compare 2-5 models across standard dimensions.

        Args:
            models: List of ModelCatalog entries (2-5).
            hardware: Optional hardware profile for speed/VRAM estimates.

        Returns:
            ComparisonResult with per-dimension winners and overall summary.
        """
        if len(models) < MIN_COMPARE:
            raise ValueError(f"At least {MIN_COMPARE} models required for comparison")
        if len(models) > MAX_COMPARE:
            raise ValueError(f"At most {MAX_COMPARE} models allowed for comparison")

        names = [m.display_name for m in models]
        result = ComparisonResult(models=names)

        for dim in COMPARISON_DIMENSIONS:
            dr = self._compute_dimension(dim, models, hardware)
            result.dimensions.append(dr)
            if dr.winner:
                result.dimension_wins[dr.winner] = (
                    result.dimension_wins.get(dr.winner, 0) + 1
                )

        # Overall winner: model with most dimension wins
        if result.dimension_wins:
            result.winner_model = max(
                result.dimension_wins, key=result.dimension_wins.get
            )

        result.summary = self._generate_summary(result, models, hardware)
        return result

    def _compute_dimension(
        self,
        dimension: str,
        models: list[ModelCatalog],
        hardware: HardwareProfile | None,
    ) -> DimensionResult:
        """Compute values and winner for a single dimension."""
        display_names = {
            "parameter_count": "Parameter Count",
            "context_length": "Context Length",
            "quality": "Quality Score",
            "vram_required": "VRAM Required",
            "speed": "Est. Speed (TPS)",
        }
        higher_is_better = {
            "parameter_count": True,
            "context_length": True,
            "quality": True,
            "vram_required": False,
            "speed": True,
        }

        dr = DimensionResult(
            dimension=dimension,
            display_name=display_names.get(dimension, dimension),
            higher_is_better=higher_is_better.get(dimension, True),
        )

        for model in models:
            value = self._get_dimension_value(dimension, model, hardware)
            dr.values[model.display_name] = value

        # Determine winner (only for numeric values)
        numeric_vals = {
            k: v for k, v in dr.values.items() if isinstance(v, (int, float))
        }
        if numeric_vals:
            if dr.higher_is_better:
                dr.winner = max(numeric_vals, key=numeric_vals.get)
            else:
                dr.winner = min(numeric_vals, key=numeric_vals.get)
        else:
            # Fallback: pick first non-None
            for name, val in dr.values.items():
                if val is not None:
                    dr.winner = name
                    break

        return dr

    def _get_dimension_value(
        self,
        dimension: str,
        model: ModelCatalog,
        hardware: HardwareProfile | None,
    ) -> float | None:
        """Extract a numeric value for a comparison dimension."""
        if dimension == "parameter_count":
            return model.parameter_count

        if dimension == "context_length":
            return float(model.context_length_default or 0) or None

        if dimension == "quality":
            best_quant = self._best_quantization(model)
            return get_quantization_quality(best_quant)

        if dimension == "vram_required":
            param_count = model.parameter_count or 7.0
            best_quant = self._best_quantization(model)
            return estimate_vram_gb(param_count, best_quant)

        if dimension == "speed":
            if hardware is None:
                return None
            param_count = model.parameter_count or 7.0
            best_quant = self._best_quantization(model)
            vram = estimate_vram_gb(param_count, best_quant)
            if hardware.gpu_available and hardware.gpu_memory_bandwidth_gbps:
                tps = hardware.gpu_memory_bandwidth_gbps / (2 * vram)
                return min(tps, 200.0)
            return None

        return None

    def _best_quantization(self, model: ModelCatalog) -> str:
        """Pick the best quantization available for a model."""
        if model.variants:
            best = max(model.variants, key=lambda v: v.quality_score or 0)
            return best.quantization
        return "Q4_K_M"

    def _generate_summary(
        self,
        result: ComparisonResult,
        models: list[ModelCatalog],
        hardware: HardwareProfile | None,
    ) -> str:
        """Generate a human-readable summary of the comparison."""
        parts: list[str] = []

        if result.winner_model:
            wins = result.dimension_wins[result.winner_model]
            total = len(COMPARISON_DIMENSIONS)
            parts.append(
                f"{result.winner_model} wins {wins}/{total} dimensions."
            )

        for dim in result.dimensions:
            if dim.winner:
                parts.append(f"{dim.display_name}: {dim.winner} leads.")

        if not parts:
            return "Models are closely matched across all dimensions."

        return " ".join(parts)
