"""Tests for context compactor — compaction logic and token estimation."""

from __future__ import annotations

from backend.app.agents.compactor import (
    ContextCompactor,
    CompactionResult,
    _fallback_compact,
    compact_context,
    estimate_token_count,
)


class TestEstimateTokenCount:
    """Token estimation for compaction triggers."""

    def test_empty_history(self):
        assert estimate_token_count([]) == 0

    def test_single_message(self):
        msgs = [{"role": "user", "content": "hello world"}]
        # "hello world" ≈ 10 chars at 4 chars/token = ~2, + 10 overhead = ~12/4 = ~3
        est = estimate_token_count(msgs)
        assert est > 0

    def test_multiple_messages(self):
        msgs = [
            {"role": "user", "content": "Hello, what is the weather?"},
            {"role": "assistant", "content": "The weather is sunny."},
        ]
        est = estimate_token_count(msgs)
        assert est > 0

    def test_longer_text_more_tokens(self):
        short = estimate_token_count([{"role": "user", "content": "hello"}])
        long = estimate_token_count([{"role": "user", "content": "hello " * 200}])
        assert long > short

    def test_overhead_added(self):
        empty = [{"role": "user", "content": ""}]
        est = estimate_token_count(empty)
        # Empty content gets at least overhead tokens for the role marker
        assert est > 0


class TestFallbackCompact:
    """Fallback compaction when LLM unavailable."""

    def test_empty_history(self):
        assert _fallback_compact([]) == ""

    def test_single_turn(self):
        result = _fallback_compact([{"role": "user", "content": "Hello world"}])
        assert "GOAL:" in result
        assert "Hello world" in result

    def test_multiple_turns(self):
        history = [
            {"role": "user", "content": "Find the bug"},
            {"role": "assistant", "content": "Looking..."},
            {"role": "tool", "content": "Result: found it"},
        ]
        result = _fallback_compact(history)
        assert "GOAL:" in result
        assert "DONE:" in result
        assert "STATE:" in result
        assert "PENDING:" in result
        assert "Find the bug" in result
        assert "found it" in result


class TestCompactContext:
    """Context compaction with optional LLM."""

    async def test_empty_history(self):
        result = await compact_context([])
        assert result == ""

    async def test_fallback_no_llm(self):
        history = [{"role": "user", "content": "Search for x"}]
        result = await compact_context(history, llm_chat=None)
        assert "GOAL:" in result
        assert "Search for x" in result

    async def test_llm_fallback_on_error(self):
        """When llm_chat is provided but raises, should fall back gracefully."""

        async def broken_chat(**kwargs):
            raise RuntimeError("LLM unavailable")

        history = [{"role": "user", "content": "Test message"}]
        result = await compact_context(history, llm_chat=broken_chat)
        assert "GOAL:" in result
        assert "Test message" in result


class TestContextCompactor:
    """ContextCompactor class — stateful compaction with stats."""

    def test_should_compact_below_threshold(self):
        compactor = ContextCompactor(threshold=0.85, max_tokens=1000)
        history = [{"role": "user", "content": "short"}]
        assert compactor.should_compact(history) is False

    def test_should_compact_above_threshold(self):
        compactor = ContextCompactor(threshold=0.85, max_tokens=10)
        history = [{"role": "user", "content": "x " * 200}]
        assert compactor.should_compact(history) is True

    def test_compact_fallback_no_llm(self):
        compactor = ContextCompactor(max_tokens=1000)
        history = [
            {"role": "user", "content": "Find the bug"},
            {"role": "assistant", "content": "Looking..."},
        ]
        result = compactor.compact_sync(history)
        assert isinstance(result, CompactionResult)
        assert "GOAL:" in result.summary
        assert result.tokens_before > 0
        assert result.tokens_after > 0
        # For short conversations, fallback summary may be longer than input (negative ratio)
        assert isinstance(result.reduction_ratio, float)

    def test_parse_sections(self):
        compactor = ContextCompactor(max_tokens=1000)
        summary = (
            "GOAL: Fix the authentication bug\n"
            "DONE: Found the root cause\n"
            "STATE: About to apply the fix\n"
            "PENDING: Write tests and commit"
        )
        sections = compactor._parse_sections(summary)
        assert sections["goal"] == "Fix the authentication bug"
        assert sections["done"] == "Found the root cause"
        assert sections["state"] == "About to apply the fix"
        assert sections["pending"] == "Write tests and commit"

    def test_stats_tracking(self):
        compactor = ContextCompactor(max_tokens=1000)
        history = [{"role": "user", "content": "Test " * 100}]
        compactor.compact_sync(history)
        compactor.compact_sync(history)
        stats = compactor.get_stats()
        assert stats["compaction_count"] == 2
        assert stats["total_tokens_saved"] >= 0
        assert stats["threshold"] == 0.85

    def test_format_history(self):
        compactor = ContextCompactor(max_tokens=1000)
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        text = compactor._format_history(history)
        assert "[USER]" in text
        assert "Hello" in text
        assert "[ASSISTANT]" in text
