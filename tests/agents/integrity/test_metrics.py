"""Tests for metrics models."""

from backend.app.agents.integrity.model.metrics import (
    ExecutionMetrics,
    IntegrityScores,
    PerformanceMetrics,
    RepositoryAnalytics,
)


def test_integrity_scores():
    s = IntegrityScores(
        integrity_score=85.0,
        structural_score=90.0,
        semantic_score=80.0,
        evolution_score=70.0,
    )
    assert s.integrity_score == 85.0
    assert 0 <= s.structural_score <= 100


def test_execution_metrics_defaults():
    m = ExecutionMetrics()
    assert m.total_findings == 0
    assert len(m.by_severity) == 0
    assert m.coverage == 0.0


def test_repository_analytics():
    a = RepositoryAnalytics()
    assert a.dependency_density == 0.0
    assert a.cycles == 0


def test_performance_metrics():
    p = PerformanceMetrics()
    assert p.collection_time_ms == 0
    assert p.peak_memory_mb == 0.0
