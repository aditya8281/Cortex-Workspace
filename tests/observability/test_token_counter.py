"""Tests for token counting — P07 Task 1."""

from __future__ import annotations

import time

import pytest

from backend.app.agents.token_counter import CumulativeUsage, TokenCount, TokenCounter


class TestTokenCounterInit:
    def test_default_model(self):
        counter = TokenCounter()
        assert counter.model == "default"
        assert counter.max_context_tokens == 8192

    def test_known_model(self):
        counter = TokenCounter(model="gpt-4o")
        assert counter.max_context_tokens == 128_000

    def test_unknown_model_fallback(self):
        counter = TokenCounter(model="nonexistent-model-xyz")
        assert counter.max_context_tokens == 8192


class TestTokenCounterCounting:
    @pytest.mark.asyncio
    async def test_count_tokens_basic(self):
        counter = TokenCounter()
        messages = [{"role": "user", "content": "Hello world"}]
        count = await counter.count_tokens(messages)
        assert count > 0

    @pytest.mark.asyncio
    async def test_count_tokens_multi_message(self):
        counter = TokenCounter()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        count = await counter.count_tokens(messages)
        assert count > 10  # 3 messages + content

    @pytest.mark.asyncio
    async def test_count_tokens_empty_content(self):
        counter = TokenCounter()
        messages = [{"role": "user", "content": ""}]
        count = await counter.count_tokens(messages)
        assert count >= 4  # at least per-message overhead

    @pytest.mark.asyncio
    async def test_count_request(self):
        counter = TokenCounter(model="gpt-4o")
        messages = [{"role": "user", "content": "What is 2+2?"}]
        result = await counter.count_request(messages, "4")
        assert isinstance(result, TokenCount)
        assert result.input_tokens > 0
        assert result.output_tokens > 0
        assert result.total_tokens == result.input_tokens + result.output_tokens
        assert result.model == "gpt-4o"
        assert result.context_window == 128_000
        assert result.context_usage_pct < 0.01  # tiny fraction


class TestTokenCounterCumulative:
    @pytest.mark.asyncio
    async def test_cumulative_updates(self):
        counter = TokenCounter()
        msgs = [{"role": "user", "content": "test message"}]

        await counter.count_request(msgs, "response one")
        await counter.count_request(msgs, "response two")

        usage = counter.get_cumulative_usage()
        assert isinstance(usage, CumulativeUsage)
        assert usage.total_requests == 2
        assert usage.total_input_tokens > 0
        assert usage.total_output_tokens > 0
        assert usage.avg_input_tokens > 0
        assert usage.avg_output_tokens > 0


class TestTokenCounterContextUsage:
    def test_context_usage_percentage(self):
        counter = TokenCounter(model="gpt-4")
        messages = [{"role": "user", "content": "Hello world"}]
        pct = counter.get_context_usage(messages)
        assert 0.0 < pct < 1.0

    def test_context_usage_empty(self):
        counter = TokenCounter()
        pct = counter.get_context_usage([])
        assert pct == 0.0

    def test_set_model(self):
        counter = TokenCounter()
        assert counter.max_context_tokens == 8192
        counter.set_model("gpt-4o")
        assert counter.max_context_tokens == 128_000
        assert counter.model == "gpt-4o"


class TestTokenCounterPerformance:
    @pytest.mark.asyncio
    async def test_counting_speed(self):
        """Token counting should be fast — < 50ms for a typical message."""
        counter = TokenCounter()
        messages = [{"role": "user", "content": "Hello, this is a test message with some content."}]
        start = time.monotonic()
        for _ in range(100):
            await counter.count_tokens(messages)
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 5000  # 100 counts in under 5s = <50ms each
