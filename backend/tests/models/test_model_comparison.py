"""Tests for model comparison service."""

import pytest

from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant
from backend.app.services.awareness.hardware import HardwareProfile
from backend.app.services.intelligence.model_comparison import (
    COMPARISON_DIMENSIONS,
    ComparisonResult,
    ModelComparisonService,
)


def _make_hardware(**kwargs) -> HardwareProfile:
    defaults = {
        "ram_total_gb": 32.0,
        "ram_available_gb": 24.0,
        "cpu_count": 8,
        "cpu_threads": 16,
        "gpu_available": True,
        "gpu_name": "RTX 4090",
        "gpu_type": "nvidia",
        "vram_total_gb": 24.0,
        "vram_available_gb": 20.0,
        "gpu_memory_bandwidth_gbps": 1008.0,
        "gpu_compute_capability": "8.9",
        "disk_free_gb": 500.0,
        "supports_cuda": True,
    }
    defaults.update(kwargs)
    return HardwareProfile(**defaults)  # type: ignore[arg-type]


def _make_model(**kwargs) -> ModelCatalog:
    defaults = {
        "model_id": "test-model",
        "family": "test",
        "display_name": "Test Model",
        "provider": "ollama",
        "parameter_count": 7.0,
        "context_length_default": 4096,
        "context_length_max": 32768,
        "capabilities": ["chat"],
        "description": "A test model",
    }
    defaults.update(kwargs)
    return ModelCatalog(**defaults)


def _make_variant(**kwargs) -> ModelVariant:
    defaults = {
        "model_catalog_id": 0,
        "variant_id": "test-variant",
        "quantization": "Q4_K_M",
        "parameter_count": 7.0,
        "size_bytes": 4_000_000_000,
        "size_gb": 4.0,
        "vram_required_gb": 5.0,
        "ram_required_gb": 6.0,
        "recommended_vram_gb": 6.5,
        "quality_score": 85.0,
        "downloaded": False,
    }
    defaults.update(kwargs)
    return ModelVariant(**defaults)


def test_compare_rejects_too_few_models():
    svc = ModelComparisonService()
    model = _make_model()
    with pytest.raises(ValueError, match="At least 2"):
        svc.compare([model])


def test_compare_rejects_too_many_models():
    svc = ModelComparisonService()
    models = [_make_model(model_id=f"m-{i}", display_name=f"Model {i}") for i in range(6)]
    with pytest.raises(ValueError, match="At most 5"):
        svc.compare(models)


def test_compare_two_models():
    svc = ModelComparisonService()
    small = _make_model(
        model_id="small",
        display_name="Small 3B",
        parameter_count=3.0,
        context_length_default=8192,
    )
    large = _make_model(
        model_id="large",
        display_name="Large 70B",
        parameter_count=70.0,
        context_length_default=128000,
    )
    result = svc.compare([small, large])

    assert isinstance(result, ComparisonResult)
    assert len(result.models) == 2
    assert len(result.dimensions) == len(COMPARISON_DIMENSIONS)
    assert result.winner_model is not None
    assert result.winner_model in result.models
    assert len(result.summary) > 0


def test_compare_dimensions_have_correct_names():
    svc = ModelComparisonService()
    m1 = _make_model(model_id="m1", display_name="M1")
    m2 = _make_model(model_id="m2", display_name="M2")
    result = svc.compare([m1, m2])

    dim_names = [d.dimension for d in result.dimensions]
    assert dim_names == COMPARISON_DIMENSIONS


def test_parameter_count_dimension():
    svc = ModelComparisonService()
    small = _make_model(model_id="small", display_name="Small", parameter_count=3.0)
    large = _make_model(model_id="large", display_name="Large", parameter_count=70.0)
    result = svc.compare([small, large])

    pc = next(d for d in result.dimensions if d.dimension == "parameter_count")
    assert pc.winner == "Large"
    assert pc.values["Large"] == 70.0
    assert pc.values["Small"] == 3.0
    assert pc.higher_is_better is True


def test_context_length_dimension():
    svc = ModelComparisonService()
    short_ctx = _make_model(model_id="short", display_name="Short", context_length_default=4096)
    long_ctx = _make_model(model_id="long", display_name="Long", context_length_default=200000)
    result = svc.compare([short_ctx, long_ctx])

    cl = next(d for d in result.dimensions if d.dimension == "context_length")
    assert cl.winner == "Long"


def test_vram_required_lower_is_better():
    svc = ModelComparisonService()
    light = _make_model(model_id="light", display_name="Light", parameter_count=3.0)
    heavy = _make_model(model_id="heavy", display_name="Heavy", parameter_count=70.0)
    result = svc.compare([light, heavy])

    vram = next(d for d in result.dimensions if d.dimension == "vram_required")
    assert vram.higher_is_better is False
    assert vram.winner == "Light"


def test_speed_dimension_with_hardware():
    svc = ModelComparisonService()
    hw = _make_hardware()
    fast = _make_model(model_id="fast", display_name="Fast", parameter_count=3.0)
    slow = _make_model(model_id="slow", display_name="Slow", parameter_count=70.0)
    result = svc.compare([fast, slow], hardware=hw)

    speed = next(d for d in result.dimensions if d.dimension == "speed")
    assert speed.winner == "Fast"
    assert speed.values["Fast"] is not None
    assert speed.values["Slow"] is not None
    assert speed.values["Fast"] > speed.values["Slow"]


def test_speed_dimension_without_hardware():
    svc = ModelComparisonService()
    m1 = _make_model(model_id="m1", display_name="M1")
    m2 = _make_model(model_id="m2", display_name="M2")
    result = svc.compare([m1, m2])

    speed = next(d for d in result.dimensions if d.dimension == "speed")
    assert speed.values["M1"] is None
    assert speed.values["M2"] is None


def test_quality_dimension():
    svc = ModelComparisonService()
    m1 = _make_model(model_id="m1", display_name="M1")
    m1.variants = [_make_variant(quantization="Q4_K_M", quality_score=85.0)]
    m2 = _make_model(model_id="m2", display_name="M2")
    m2.variants = [_make_variant(quantization="Q8_0", quality_score=98.0)]
    result = svc.compare([m1, m2])

    quality = next(d for d in result.dimensions if d.dimension == "quality")
    assert quality.winner == "M2"


def test_dimension_wins_accumulation():
    svc = ModelComparisonService()
    dominant = _make_model(
        model_id="dominant",
        display_name="Dominant",
        parameter_count=70.0,
        context_length_default=200000,
    )
    weak = _make_model(
        model_id="weak",
        display_name="Weak",
        parameter_count=3.0,
        context_length_default=2048,
    )
    result = svc.compare([dominant, weak])

    assert result.dimension_wins.get("Dominant", 0) >= 2
    assert result.winner_model == "Dominant"


def test_three_way_comparison():
    svc = ModelComparisonService()
    models = [
        _make_model(model_id="a", display_name="A", parameter_count=3.0, context_length_default=4096),
        _make_model(model_id="b", display_name="B", parameter_count=8.0, context_length_default=32000),
        _make_model(model_id="c", display_name="C", parameter_count=70.0, context_length_default=128000),
    ]
    result = svc.compare(models)

    assert len(result.models) == 3
    assert result.winner_model in ["A", "B", "C"]
    assert len(result.dimension_wins) > 0


def test_summary_is_non_empty():
    svc = ModelComparisonService()
    m1 = _make_model(model_id="m1", display_name="M1")
    m2 = _make_model(model_id="m2", display_name="M2")
    result = svc.compare([m1, m2])

    assert isinstance(result.summary, str)
    assert len(result.summary) > 0


def test_compare_with_variants_uses_best_quant():
    svc = ModelComparisonService()
    m1 = _make_model(model_id="m1", display_name="M1")
    m1.variants = [
        _make_variant(quantization="Q4_K_M", quality_score=85.0),
        _make_variant(quantization="Q8_0", quality_score=98.0),
    ]
    m2 = _make_model(model_id="m2", display_name="M2")
    m2.variants = [_make_variant(quantization="Q4_K_M", quality_score=85.0)]

    result = svc.compare([m1, m2])
    quality = next(d for d in result.dimensions if d.dimension == "quality")
    # M1 has Q8_0 (98) > M2 Q4_K_M (85)
    assert quality.winner == "M1"


def test_five_model_comparison():
    svc = ModelComparisonService()
    models = [_make_model(model_id=f"m{i}", display_name=f"Model{i}", parameter_count=2**i) for i in range(1, 6)]
    result = svc.compare(models)
    assert len(result.models) == 5
    assert result.winner_model is not None


def test_result_dataclass_fields():
    svc = ModelComparisonService()
    m1 = _make_model(model_id="m1", display_name="M1")
    m2 = _make_model(model_id="m2", display_name="M2")
    result = svc.compare([m1, m2])

    assert hasattr(result, "models")
    assert hasattr(result, "dimensions")
    assert hasattr(result, "winner_model")
    assert hasattr(result, "dimension_wins")
    assert hasattr(result, "summary")
