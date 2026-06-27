"""Tests for tool execution timing — P07 Task 4."""

from __future__ import annotations

import time

from backend.app.agents.tools.timing import ToolTimingRecord, ToolTimingTracker


class TestToolTimingStart:
    def test_start_creates_record(self):
        tracker = ToolTimingTracker()
        record = tracker.start("read_file")
        assert isinstance(record, ToolTimingRecord)
        assert record.tool_name == "read_file"
        assert record.start_time > 0

    def test_start_mcp_tool(self):
        tracker = ToolTimingTracker()
        record = tracker.start("mcp_srv_read", is_mcp=True, mcp_server="srv")
        assert record.is_mcp is True
        assert record.mcp_server == "srv"


class TestToolTimingFinish:
    def test_finish_records_duration(self):
        tracker = ToolTimingTracker()
        record = tracker.start("test_tool")
        time.sleep(0.01)
        record.success = True
        finished = tracker.finish(record)
        assert finished.duration_ms >= 5
        assert finished.end_time > 0

    def test_finish_stores_record(self):
        tracker = ToolTimingTracker()
        record = tracker.start("test_tool")
        time.sleep(0.01)
        tracker.finish(record)
        stats = tracker.get_tool_stats("test_tool")
        assert stats["executions"] == 1


class TestToolTimingStats:
    def test_tool_stats_basic(self):
        tracker = ToolTimingTracker()
        for i in range(5):
            record = tracker.start("tool_a")
            time.sleep(0.005)
            record.success = i != 2  # fail on 3rd
            tracker.finish(record)

        stats = tracker.get_tool_stats("tool_a")
        assert stats["tool"] == "tool_a"
        assert stats["executions"] == 5
        assert stats["successes"] == 4
        assert stats["failures"] == 1
        assert stats["success_rate"] == 0.8
        assert stats["avg_ms"] > 0
        assert stats["p50_ms"] > 0
        assert stats["min_ms"] > 0
        assert stats["max_ms"] >= stats["min_ms"]

    def test_tool_stats_empty(self):
        tracker = ToolTimingTracker()
        stats = tracker.get_tool_stats("nonexistent")
        assert stats["executions"] == 0

    def test_all_stats(self):
        tracker = ToolTimingTracker()
        r1 = tracker.start("tool_a")
        tracker.finish(r1)
        r2 = tracker.start("tool_b")
        tracker.finish(r2)

        all_stats = tracker.get_all_stats()
        assert "tool_a" in all_stats
        assert "tool_b" in all_stats

    def test_slow_tools(self):
        tracker = ToolTimingTracker()
        record = tracker.start("slow_tool")
        record.duration_ms = 2000
        tracker.finish(record)

        slow = tracker.get_slow_tools(threshold_ms=1000)
        assert len(slow) == 1
        assert slow[0]["tool"] == "slow_tool"


class TestToolTimingReset:
    def test_reset_clears_all(self):
        tracker = ToolTimingTracker()
        record = tracker.start("test")
        tracker.finish(record)
        tracker.reset()
        assert tracker.get_tool_stats("test")["executions"] == 0
