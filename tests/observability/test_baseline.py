"""Tests for performance baseline — P07 Task 6."""

from __future__ import annotations

import pytest

from backend.app.agents.baseline import BaselineMetrics, PerformanceBaseline
from backend.app.agents.tools.timing import ToolTimingTracker
from backend.app.agents.tps_tracker import TPSTracker


class TestBaselineMetrics:
    def test_default_values(self):
        metrics = BaselineMetrics()
        assert metrics.first_token_latency_ms == 0
        assert metrics.avg_tool_latency_ms == 0
        assert metrics.avg_tps == 0
        assert metrics.memory_rss_mb == 0
        assert metrics.sample_size == 0


class TestPerformanceBaseline:
    @pytest.mark.asyncio
    async def test_capture_basic(self):
        baseline = PerformanceBaseline()
        metrics = await baseline.capture()
        assert isinstance(metrics, BaselineMetrics)
        assert metrics.captured_at != ""

    @pytest.mark.asyncio
    async def test_capture_with_tool_timing(self):
        tracker = ToolTimingTracker()
        record = tracker.start("test_tool")
        record.success = True
        tracker.finish(record)

        baseline = PerformanceBaseline(tool_timing=tracker)
        metrics = await baseline.capture()
        assert metrics.avg_tool_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_capture_with_tps(self):
        tps = TPSTracker()
        tps.start()
        tps.on_token(count=10)
        tps.finish()

        baseline = PerformanceBaseline(tps_tracker=tps)
        metrics = await baseline.capture()
        assert metrics.avg_tps >= 0

    @pytest.mark.asyncio
    async def test_compare_returns_dict(self):
        baseline = PerformanceBaseline()
        metrics = await baseline.capture()
        comparison = await baseline.compare(metrics)
        assert isinstance(comparison, dict)
        assert "avg_tps" in comparison
        assert "memory_rss_mb" in comparison

    @pytest.mark.asyncio
    async def test_capture_has_resource_metrics(self):
        baseline = PerformanceBaseline()
        metrics = await baseline.capture()
        assert metrics.memory_rss_mb >= 0
        assert metrics.cpu_percent >= 0
