"""Tests for completion verifier — heuristic and LLM-based verification."""

from __future__ import annotations

from backend.app.agents.verifier import _heuristic_verdict, _parse_verdict, verify_completion


class TestHeuristicVerdict:
    """Fallback heuristic when no LLM available."""

    def test_empty_response(self):
        v = _heuristic_verdict("")
        assert v.complete is False

    def test_error_indicators(self):
        v = _heuristic_verdict("I don't know how to do that")
        assert v.complete is False

    def test_uncertainty(self):
        v = _heuristic_verdict("I'm not sure about this")
        assert v.complete is False

    def test_short_response(self):
        v = _heuristic_verdict("Yes")
        assert v.complete is False  # too short

    def test_normal_response(self):
        v = _heuristic_verdict(
            "Here's the result of the search. I found 3 files and they contain the data you requested."
        )
        assert v.complete is True

    def test_complete_with_fallback(self):
        v = _heuristic_verdict("Task complete. I've found the information you requested.")
        assert v.complete is True


class TestParseVerdict:
    """Parse LLM verdict format."""

    def test_parse_complete(self):
        text = "VERDICT: COMPLETE\nSUMMARY: Found the file\nFEEDBACK: All good"
        v = _parse_verdict(text)
        assert v.complete is True
        assert v.summary == "Found the file"
        assert v.feedback == "All good"

    def test_parse_incomplete(self):
        text = "VERDICT: INCOMPLETE\nSUMMARY: Missing data\nFEEDBACK: Need more info"
        v = _parse_verdict(text)
        assert v.complete is False

    def test_parse_needs_more(self):
        text = "VERDICT: NEEDS_MORE\nSUMMARY: Partial result\nFEEDBACK: Continue searching"
        v = _parse_verdict(text)
        assert v.complete is False

    def test_parse_no_verdict(self):
        text = "Some random text"
        v = _parse_verdict(text)
        assert v.complete is False


class TestVerifyCompletionIntegration:
    """Integration tests — verify_completion with different inputs."""

    async def test_without_llm_returns_heuristic(self):
        v = await verify_completion(
            original_message="find file X",
            conversation_history=[{"role": "user", "content": "find file X"}],
            final_response="Here is file X: it contains the data.",
        )
        # Should use heuristic (no llm_chat)
        assert isinstance(v.complete, bool)
        assert v.summary

    async def test_empty_response_without_llm(self):
        v = await verify_completion(
            original_message="do something",
            conversation_history=[],
            final_response="",
        )
        assert v.complete is False
