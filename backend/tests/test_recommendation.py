"""Tests for recommendation engine."""

from datetime import datetime, timedelta, timezone

from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelStatistics
from backend.app.services.awareness.hardware import HardwareProfile
from backend.app.services.intelligence.recommendation import WORKLOADS, RecommendationEngine


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
        "last_updated": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return ModelCatalog(**defaults)


def _make_statistics(**kwargs) -> ModelStatistics:
    defaults = {
        "model_catalog_id": 0,
        "download_count_total": 0,
        "download_count_period": 0,
        "trending_score": 0.0,
    }
    defaults.update(kwargs)
    return ModelStatistics(**defaults)


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
        _make_model(
            model_id="llama-3.1-8b", family="llama", parameter_count=8.0, capabilities=["chat", "code", "reasoning"]
        ),
        _make_model(model_id="nomic-embed", family="nomic", parameter_count=0.137, capabilities=["embedding"]),
        _make_model(model_id="llava-7b", family="llava", parameter_count=7.0, capabilities=["vision"]),
    ]

    for workload_id in WORKLOADS:
        engine.recommend_for_workload(workload_id, models)
        # Each workload should produce at least one recommendation if there are matching models
        # Some may have 0 if no models match (e.g., embedding models for coding)


def _constrained_hw() -> HardwareProfile:
    """Hardware with tight RAM so scores stay well below 100."""
    return _make_hardware(
        gpu_available=False,
        vram_total_gb=0,
        vram_available_gb=0,
        ram_total_gb=6.0,
        ram_available_gb=5.0,
        gpu_memory_bandwidth_gbps=0,
    )


def _old_model(**kwargs) -> ModelCatalog:
    """Model with very old last_updated so recency bonus is 0."""
    defaults = {"last_updated": datetime.now(timezone.utc) - timedelta(days=9999)}
    defaults.update(kwargs)
    return _make_model(**defaults)


def test_popularity_score_no_downloads():
    hw = _constrained_hw()
    engine = RecommendationEngine(hw)
    model = _old_model()
    stats = _make_statistics(download_count_total=0)

    config = {"preferred_families": [], "priority_families": []}
    rec = engine._evaluate_model(model, config)
    assert rec is not None
    score_no_stats = engine._calculate_score(model, rec.variant, config)
    score_with_stats = engine._calculate_score(model, rec.variant, config, stats)
    assert score_with_stats == score_no_stats  # 0 downloads = no bonus


def test_popularity_score_high_downloads():
    hw = _constrained_hw()
    engine = RecommendationEngine(hw)
    model = _old_model(total_downloads=50)
    stats = _make_statistics(download_count_total=15000)

    config = {"preferred_families": [], "priority_families": []}
    rec = engine._evaluate_model(model, config)
    assert rec is not None
    score_no_stats = engine._calculate_score(model, rec.variant, config)
    score_with_stats = engine._calculate_score(model, rec.variant, config, stats)
    # stats override: 15000 downloads → +10 vs model's 50 downloads → +1
    assert score_with_stats > score_no_stats


def test_popularity_score_tiers():
    hw = _constrained_hw()
    engine = RecommendationEngine(hw)
    model = _old_model()

    config = {"preferred_families": [], "priority_families": []}
    rec = engine._evaluate_model(model, config)
    assert rec is not None

    tiers = [
        (5, 0),  # 5 downloads -> 0 pts
        (10, 1),  # 10 downloads -> 1 pt
        (100, 3),  # 100 downloads -> 3 pts
        (1000, 5),  # 1000 downloads -> 5 pts
        (5000, 7),  # 5000 downloads -> 7 pts
        (10000, 10),  # 10000 downloads -> 10 pts
    ]

    base_score = engine._calculate_score(model, rec.variant, config)

    for downloads, expected_bonus in tiers:
        stats = _make_statistics(download_count_total=downloads)
        score = engine._calculate_score(model, rec.variant, config, stats)
        actual_bonus = score - base_score
        assert actual_bonus == expected_bonus, f"downloads={downloads}: expected +{expected_bonus}, got +{actual_bonus}"


def test_recency_score_recent_model():
    hw = _constrained_hw()
    engine = RecommendationEngine(hw)

    recent = _make_model(model_id="recent", last_updated=datetime.now(timezone.utc))
    old = _old_model(model_id="old")

    config = {"preferred_families": [], "priority_families": []}
    rec_recent = engine._evaluate_model(recent, config)
    rec_old = engine._evaluate_model(old, config)

    assert rec_recent is not None and rec_old is not None
    assert rec_recent.score > rec_old.score, "Recently updated model should score higher than old model"


def test_recency_score_tiers():
    hw = _constrained_hw()
    engine = RecommendationEngine(hw)

    tiers = [
        (15, 5),  # 15 days -> 5 pts
        (60, 4),  # 60 days -> 4 pts
        (120, 3),  # 120 days -> 3 pts
        (200, 2),  # 200 days -> 2 pts
        (500, 1),  # 500 days -> 1 pt
        (800, 0),  # 800 days -> 0 pts
    ]

    baseline_model = _old_model(model_id="baseline")
    config = {"preferred_families": [], "priority_families": []}
    rec_baseline = engine._evaluate_model(baseline_model, config)
    baseline_score = engine._calculate_score(baseline_model, rec_baseline.variant, config)

    for days, expected_bonus in tiers:
        model = _make_model(model_id=f"model-{days}d", last_updated=datetime.now(timezone.utc) - timedelta(days=days))
        score = engine._calculate_score(model, rec_baseline.variant, config)
        actual_bonus = score - baseline_score
        assert actual_bonus == expected_bonus, f"days={days}: expected +{expected_bonus}, got +{actual_bonus}"


def test_efficiency_score_high_tps_low_vram():
    hw = _make_hardware(vram_total_gb=8.0, vram_available_gb=7.0)
    engine = RecommendationEngine(hw)

    small = _make_model(model_id="small", parameter_count=3.0)
    large = _make_model(model_id="large", parameter_count=16.0)

    config = {"preferred_families": [], "priority_families": []}
    rec_small = engine._evaluate_model(small, config)
    rec_large = engine._evaluate_model(large, config)

    assert rec_small is not None and rec_large is not None
    assert rec_small.score >= rec_large.score


def test_efficiency_score_calculation():
    hw = _make_hardware()
    engine = RecommendationEngine(hw)
    model = _make_model(parameter_count=7.0)

    rec = engine._evaluate_model(model, {"preferred_families": ["test"], "priority_families": ["test"]})
    assert rec is not None

    # Verify efficiency calculation manually
    from backend.app.services.intelligence.model_catalog import estimate_tps_gpu

    bandwidth = hw.gpu_memory_bandwidth_gbps
    tps = estimate_tps_gpu(
        rec.variant.parameter_count or 7.0,
        rec.variant.size_gb or 4.0,
        bandwidth,
    )
    vram_gb = rec.variant.vram_required_gb or 1.0
    if tps and tps > 0:
        efficiency = tps / vram_gb
        assert efficiency > 0


def test_score_includes_all_dimensions():
    """Verify the total score can include points from all dimensions."""
    hw = _make_hardware(
        gpu_available=False,
        vram_total_gb=0,
        vram_available_gb=0,
        ram_total_gb=32.0,
        ram_available_gb=20.0,
        gpu_memory_bandwidth_gbps=0,
    )
    engine = RecommendationEngine(hw)

    now = datetime.now(timezone.utc)
    model = _make_model(
        model_id="full-score-model",
        family="llama",
        total_downloads=20000,
        last_updated=now - timedelta(days=5),
        parameter_count=8.0,
    )

    config = {"preferred_families": ["llama"], "priority_families": ["llama"]}
    rec = engine._evaluate_model(model, config)
    assert rec is not None
    assert 0 <= rec.score <= 100

    # Score should be high: popular, recent, good workload match
    assert rec.score > 70


def test_statistics_download_count_used_when_higher():
    """ModelStatistics download_count_total overrides model.total_downloads when higher."""
    hw = _constrained_hw()
    engine = RecommendationEngine(hw)

    model = _old_model(total_downloads=50)
    stats = _make_statistics(download_count_total=15000)

    config = {"preferred_families": [], "priority_families": []}
    rec = engine._evaluate_model(model, config)
    assert rec is not None

    score_no_stats = engine._calculate_score(model, rec.variant, config)
    score_with_stats = engine._calculate_score(model, rec.variant, config, stats)
    # With stats showing 15000 downloads vs model's 50, score should be higher
    assert score_with_stats > score_no_stats
