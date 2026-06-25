"""Metrics models — integrity scores, analytics, performance, execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntegrityScores:
    integrity_score: float = 0.0
    structural_score: float = 0.0
    semantic_score: float = 0.0
    evolution_score: float = 0.0


@dataclass
class RepositoryAnalytics:
    dependency_density: float = 0.0
    fan_in_distribution: dict[str, int] = field(default_factory=dict)
    fan_out_distribution: dict[str, int] = field(default_factory=dict)
    architectural_hotspots: list[str] = field(default_factory=list)
    coupling_coefficient: float = 0.0
    cycles: int = 0


@dataclass
class PerformanceMetrics:
    collection_time_ms: int = 0
    view_build_time_ms: int = 0
    analysis_time_ms: int = 0
    peak_memory_mb: float = 0.0


@dataclass
class ExecutionMetrics:
    total_findings: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_classification: dict[str, int] = field(default_factory=dict)
    by_engine: dict[str, int] = field(default_factory=dict)
    coverage: float = 0.0
    confidence_distribution: list[float] = field(default_factory=list)
