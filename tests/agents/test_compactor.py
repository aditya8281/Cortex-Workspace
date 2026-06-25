"""Tests for context compactor — compaction logic and token estimation."""

from __future__ import annotations

from backend.app.agents.compactor import _fallback_compact, compact_context, estimate_token_count


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
