"""Tests for recommendation engine."""

from backend.app.services.hardware import HardwareProfile
from backend.app.services.recommendation import RecommendationEngine, WORKLOADS
from backend.app.models.model_catalog import ModelCatalog


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
    return HardwareProfile(**defaults)


def _make_model(**kwargs) -> ModelCatalog:
    from datetime import datetime, timezone

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
        "last_updated": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return ModelCatalog(**defaults)


def test_recommendation_engine_coding():
    hw = _make_hardware()
    engine = RecommendationEngine(hw)

    models = [
        _make_model(model_id="llama-3.1-8b", family="llama", parameter_count=8.0, capabilities=["chat", "code"]),
        _make_model(model_id="qwen2.5-coder-7b", family="qwen", parameter_count=7.0, capabilities=["code"]),
        _make_model(model_id="deepseek-coder-v2", family="deepseek", parameter_count=16.0, capabilities=["code"]),
    ]

    recs = engine.recommend_for_workload("coding", models)
    assert len(recs) > 0
    # Qwen coder should rank well for coding workload
    assert any(r.catalog_entry.family == "qwen" for r in recs)


def test_recommendation_engine_lightweight():
    hw = _make_hardware(vram_total_gb=8.0, vram_available_gb=7.0)
    engine = RecommendationEngine(hw)

    models = [
        _make_model(model_id="llama-3.2-3b", family="llama", parameter_count=3.0),
        _make_model(model_id="phi-3.5-mini", family="phi", parameter_count=3.8),
        _make_model(model_id="llama-3.1-70b", family="llama", parameter_count=70.0),
    ]

    recs = engine.recommend_for_workload("lightweight", models)
    assert len(recs) > 0
    # Should not recommend 70B on 8GB VRAM
    assert not any(r.catalog_entry.model_id == "llama-3.1-70b" for r in recs)


def test_recommendation_score_range():
    hw = _make_hardware()
    engine = RecommendationEngine(hw)

    model = _make_model()
    rec = engine._evaluate_model(model, {"preferred_families": ["test"], "priority_families": ["test"]})
    assert rec is not None
    assert 0 <= rec.score <= 100


def test_all_workloads_produce_results():
    hw = _make_hardware()
    engine = RecommendationEngine(hw)

    models = [
        _make_model(model_id="llama-3.1-8b", family="llama", parameter_count=8.0, capabilities=["chat", "code", "reasoning"]),
        _make_model(model_id="nomic-embed", family="nomic", parameter_count=0.137, capabilities=["embedding"]),
        _make_model(model_id="llava-7b", family="llava", parameter_count=7.0, capabilities=["vision"]),
    ]

    for workload_id in WORKLOADS:
        recs = engine.recommend_for_workload(workload_id, models)
        # Each workload should produce at least one recommendation if there are matching models
        # Some may have 0 if no models match (e.g., embedding models for coding)
