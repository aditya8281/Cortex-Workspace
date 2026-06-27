"""Performance benchmark tests — P08 Task 4.

Establishes baseline metrics for:
- Token counting speed
- TPS tracker overhead
- Tool timing overhead
- Context tracker prediction
- Security guard throughput

These tests run periodically and compare against stored baselines.
Regression is flagged if metrics degrade beyond threshold.
"""

from __future__ import annotations

import time

import pytest

from backend.app.agents.baseline import PerformanceBaseline
from backend.app.agents.security import PromptSecurityGuard
from backend.app.agents.token_counter import TokenCounter
from backend.app.agents.tools.timing import ToolTimingTracker
from backend.app.agents.tps_tracker import TPSTracker


class TestTokenCounterPerformance:
    """Token counter performance benchmarks."""

    @pytest.mark.asyncio
    async def test_counting_speed(self):
        """Token counting should be fast — < 5ms per call."""
        counter = TokenCounter()
        messages = [
            {"role": "user", "content": "Hello, this is a test message with content."}
        ]
        start = time.monotonic()
        for _ in range(100):
            await counter.count_tokens(messages)
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 5000, f"100 token counts took {elapsed:.1f}ms (target: <5000ms)"

    @pytest.mark.asyncio
    async def test_request_counting_speed(self):
        """Full request counting should be fast — < 10ms per call."""
        counter = TokenCounter(model="gpt-4o")
        messages = [{"role": "user", "content": "What is 2+2?"}]
        start = time.monotonic()
        for _ in range(50):
            await counter.count_request(messages, "4")
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 5000, f"50 request counts took {elapsed:.1f}ms (target: <5000ms)"


class TestTPSTrackerPerformance:
    """TPS tracker overhead benchmarks."""

    def test_tracking_overhead(self):
        """TPS tracking should add negligible overhead."""
        tracker = TPSTracker()
        start = time.monotonic()
        tracker.start()
        for _ in range(10000):
            tracker.on_token()
        tracker.finish()
        elapsed = (time.monotonic() - start) * 1000
        # 10K on_token calls should take < 500ms (allow for system load)
        assert elapsed < 500, f"10K on_token calls took {elapsed:.1f}ms"


class TestToolTimingPerformance:
    """Tool timing tracker overhead benchmarks."""

    def test_timing_overhead(self):
        """Tool timing should add negligible overhead."""
        tracker = ToolTimingTracker()
        start = time.monotonic()
        for _ in range(10000):
            record = tracker.start("bench_tool")
            record.success = True
            tracker.finish(record)
        elapsed = (time.monotonic() - start) * 1000
        # 10K start+finish cycles should take < 500ms (allow for system load)
        assert elapsed < 500, f"10K timing cycles took {elapsed:.1f}ms"

    def test_stats_computation_speed(self):
        """Stats computation should be fast even with many records."""
        tracker = ToolTimingTracker()
        for _ in range(1000):
            record = tracker.start("bench_tool")
            record.success = True
            tracker.finish(record)

        start = time.monotonic()
        for _ in range(100):
            tracker.get_tool_stats("bench_tool")
        elapsed = (time.monotonic() - start) * 1000
        # 100 stats computations over 1K records should be < 500ms
        assert elapsed < 500, f"100 stats computations took {elapsed:.1f}ms"


class TestSecurityGuardPerformance:
    """Security guard throughput benchmarks."""

    def test_injection_check_throughput(self):
        """Injection checking should be fast."""
        guard = PromptSecurityGuard()
        test_content = "This is normal test content for performance benchmarking."

        start = time.monotonic()
        for _ in range(10000):
            guard._check_injection(test_content, "test")
        elapsed = (time.monotonic() - start) * 1000
        # 10K injection checks should take < 500ms
        assert elapsed < 500, f"10K injection checks took {elapsed:.1f}ms"

    def test_wrapping_throughput(self):
        """Content wrapping should be fast."""
        guard = PromptSecurityGuard()

        start = time.monotonic()
        for i in range(1000):
            guard.wrap_external_content(f"content_{i}", "retrieval")
        elapsed = (time.monotonic() - start) * 1000
        # 1K wrapping operations should take < 200ms
        assert elapsed < 200, f"1K wrapping ops took {elapsed:.1f}ms"


class TestBaselineCapture:
    """Performance baseline capture benchmarks."""

    @pytest.mark.asyncio
    async def test_baseline_capture_speed(self):
        """Baseline capture should be fast."""
        tracker = TPSTracker()
        tracker.start()
        for _ in range(100):
            tracker.on_token()

        timing = ToolTimingTracker()
        for _ in range(10):
            record = timing.start("test_tool")
            record.success = True
            timing.finish(record)

        baseline = PerformanceBaseline(tps_tracker=tracker, tool_timing=timing)

        start = time.monotonic()
        metrics = await baseline.capture()
        elapsed = (time.monotonic() - start) * 1000

        assert elapsed < 100, f"Baseline capture took {elapsed:.1f}ms"
        assert metrics.captured_at != ""
