"""Tests for enhanced completion verifier — P03 Task 6.

Enhancements over v1.01:
- VerificationResult dataclass with confidence score
- Confidence tracking stats
- Fresh context verification (no conversation history bias)
"""

from __future__ import annotations

import pytest

from backend.app.agents.verifier import (
    CompletionVerifier,
    VerificationResult,
    _heuristic_verdict,
    verify_completion,
)


class TestVerificationResultDataclass:
    """Structured verification result."""

    def test_result_fields(self):
        vr = VerificationResult(
            is_complete=True,
            confidence=0.9,
            assessment="Task fully completed",
            missing=[],
        )
        assert vr.is_complete is True
        assert vr.confidence == 0.9
        assert vr.assessment == "Task fully completed"
        assert vr.missing == []

    def test_result_incomplete(self):
        vr = VerificationResult(
            is_complete=False,
            confidence=0.3,
            assessment="Missing error handling",
            missing=["error handling", "edge cases"],
        )
        assert vr.is_complete is False
        assert len(vr.missing) == 2


class TestCompletionVerifier:
    """Fresh-context completion verifier."""

    def test_no_llm_returns_low_confidence(self):
        verifier = CompletionVerifier()
        result = verifier.verify_sync(
            original_message="Fix the bug",
            final_response="I fixed the bug in auth.py by correcting the token validation logic.",
        )
        assert result.confidence >= 0.0
        assert result.is_complete is True  # Heuristic default

    def test_empty_response_incomplete(self):
        verifier = CompletionVerifier()
        result = verifier.verify_sync(
            original_message="Fix the bug",
            final_response="",
        )
        assert result.is_complete is False
        assert result.confidence == 0.0

    def test_uncertainty_in_response(self):
        verifier = CompletionVerifier()
        result = verifier.verify_sync(
            original_message="Fix the bug",
            final_response="I don't know how to fix this issue",
        )
        assert result.is_complete is False
        assert result.confidence < 1.0

    def test_short_response_incomplete(self):
        verifier = CompletionVerifier()
        result = verifier.verify_sync(
            original_message="Implement the full authentication system with JWT tokens",
            final_response="Done. Implemented.",
        )
        assert result.is_complete is False

    def test_stats_tracking(self):
        verifier = CompletionVerifier()
        for _ in range(3):
            verifier.verify_sync(
                original_message="test",
                final_response="Completed successfully with all tests passing.",
            )
        stats = verifier.get_stats()
        assert stats["verification_count"] == 3
        assert stats["average_confidence"] > 0.0


class TestVerifyCompletionAsync:
    """Async verify_completion function."""

    @pytest.mark.asyncio
    async def test_no_llm_returns_heuristic(self):
        long_response = "The bug has been fixed in the authentication module. All tests pass now."
        history = [
            {"role": "user", "content": "Fix the bug"},
            {"role": "assistant", "content": long_response},
        ]
        result = await verify_completion(
            original_message="Fix the bug",
            conversation_history=history,
            final_response=long_response,
            llm_chat=None,
        )
        assert result.complete is True

    @pytest.mark.asyncio
    async def test_llm_error_returns_heuristic(self):
        async def broken_chat(**kwargs):
            raise RuntimeError("LLM unavailable")

        long_response = "The bug has been fixed in the authentication module. All tests pass now."
        history = [
            {"role": "user", "content": "Fix the bug"},
            {"role": "assistant", "content": long_response},
        ]
        result = await verify_completion(
            original_message="Fix the bug",
            conversation_history=history,
            final_response=long_response,
            llm_chat=broken_chat,
        )
        # Falls back to heuristic
        assert result.complete is True

    @pytest.mark.asyncio
    async def test_llm_parsing(self):
        async def mock_chat(**kwargs):
            from backend.app.services.intelligence.llm.provider import LLMResponse

            return LLMResponse(
                content="VERDICT: COMPLETE\nSUMMARY: Bug fixed in auth.py\nFEEDBACK: None",
                model="test",
            )

        long_response = "I fixed the bug in auth.py by correcting the token validation. All tests pass."
        history = [
            {"role": "user", "content": "Fix the bug"},
            {"role": "assistant", "content": long_response},
        ]
        result = await verify_completion(
            original_message="Fix the bug",
            conversation_history=history,
            final_response=long_response,
            llm_chat=mock_chat,
        )
        assert result.complete is True
        assert "Bug fixed" in result.summary


class TestHeuristicVerdict:
    """Heuristic-based verdict when no LLM available."""

    def test_empty_response(self):
        v = _heuristic_verdict("")
        assert v.complete is False

    def test_error_indicators(self):
        for phrase in ["I don't know", "error: timeout", "failed to connect"]:
            v = _heuristic_verdict(f"The result is {phrase}")
            assert v.complete is False

    def test_short_response(self):
        v = _heuristic_verdict("Done.")
        assert v.complete is False

    def test_complete_response(self):
        v = _heuristic_verdict(
            "I've completed the task. The file has been updated with the new implementation, "
            "tests pass, and the documentation has been updated."
        )
        assert v.complete is True
