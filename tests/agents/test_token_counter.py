"""Tests for tiktoken-powered token counter with fallback."""

from __future__ import annotations

from backend.app.agents.token_counter import count_message_tokens, count_tokens


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_short_string(self):
        result = count_tokens("hello")
        assert result > 0

    def test_longer_string(self):
        short = count_tokens("hello world")
        long = count_tokens("hello world " + "a" * 1000)
        assert long > short

    def test_consistency(self):
        t1 = count_tokens("hello")
        t2 = count_tokens("hello")
        assert t1 == t2


class TestCountMessageTokens:
    def test_empty_list(self):
        assert count_message_tokens([]) == 0

    def test_single_message(self):
        result = count_message_tokens([{"content": "hello world"}])
        assert result > 0

    def test_multiple_messages(self):
        msgs = [
            {"content": "hello"},
            {"content": "world " * 100},
        ]
        total = count_message_tokens(msgs)
        single = count_message_tokens([msgs[1]])
        assert total > single

    def test_messages_with_empty_content(self):
        msgs = [{"content": ""}, {"content": "hello"}]
        assert count_message_tokens(msgs) > 0

    def test_char_based_fallback_ratio(self):
        # When tiktoken is available, this uses actual encoding, not char ratio.
        # Here we just verify that longer content produces more tokens.
        short = count_message_tokens([{"content": "hello"}])
        long = count_message_tokens([{"content": "hello " * 200}])
        assert long > short
