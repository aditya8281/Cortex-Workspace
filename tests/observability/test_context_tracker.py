"""Tests for context usage tracking — P07 Task 3."""

from __future__ import annotations

import pytest

from backend.app.agents.context_tracker import ContextTracker, ContextUsageSnapshot
from backend.app.agents.token_counter import TokenCounter


@pytest.fixture()
def token_counter():
    return TokenCounter(model="gpt-4o")


@pytest.fixture()
def tracker(token_counter):
    return ContextTracker(token_counter=token_counter)


class TestContextTrackerSnapshot:
    @pytest.mark.asyncio
    async def test_snapshot_basic(self, tracker):
        messages = [{"role": "user", "content": "Hello"}]
        snap = await tracker.snapshot(messages)
        assert isinstance(snap, ContextUsageSnapshot)
        assert snap.tokens_used > 0
        assert snap.tokens_max == 128_000
        assert 0.0 < snap.usage_pct < 1.0
        assert snap.message_count == 1
        assert snap.compaction_triggered is False

    @pytest.mark.asyncio
    async def test_snapshot_history(self, tracker):
        msgs1 = [{"role": "user", "content": "msg1"}]
        msgs2 = [{"role": "user", "content": "msg2"}]

        await tracker.snapshot(msgs1)
        await tracker.snapshot(msgs2)

        history = tracker.get_usage_history()
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_snapshot_compaction_trigger(self, token_counter):
        """When context is >= 85% full, compaction should trigger."""
        tracker = ContextTracker(token_counter=token_counter)
        # Create a very large message that fills context
        large_content = "x" * (128_000 * 4)  # ~128k tokens worth of chars
        messages = [{"role": "user", "content": large_content}]
        snap = await tracker.snapshot(messages)
        # With estimation, this should trigger compaction
        assert snap.compaction_triggered is True


class TestContextTrackerCurrent:
    @pytest.mark.asyncio
    async def test_get_current_usage_empty(self, tracker):
        result = tracker.get_current_usage()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_usage_after_snapshot(self, tracker):
        messages = [{"role": "user", "content": "test"}]
        await tracker.snapshot(messages)
        current = tracker.get_current_usage()
        assert current is not None
        assert current.tokens_used > 0


class TestContextTrackerPrediction:
    @pytest.mark.asyncio
    async def test_predict_compaction_turns(self, tracker):
        messages = [{"role": "user", "content": "test"}]
        await tracker.snapshot(messages)
        turns = tracker.predict_compaction_turns(messages, avg_tokens_per_turn=500)
        assert turns > 0

    def test_predict_no_history(self, tracker):
        turns = tracker.predict_compaction_turns([], avg_tokens_per_turn=500)
        assert turns == -1


class TestContextTrackerStats:
    @pytest.mark.asyncio
    async def test_stats_empty(self, tracker):
        stats = tracker.get_stats()
        assert stats["current_usage_pct"] == 0
        assert stats["compaction_count"] == 0
        assert stats["snapshots_taken"] == 0
        assert stats["max_usage_reached"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_snapshots(self, tracker):
        messages = [{"role": "user", "content": "test"}]
        await tracker.snapshot(messages)
        stats = tracker.get_stats()
        assert stats["snapshots_taken"] == 1
        assert stats["current_usage_pct"] > 0
        assert stats["max_usage_reached"] > 0
