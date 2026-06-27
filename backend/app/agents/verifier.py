"""Completion verifier — checks whether the agent's response actually completes the task.

Uses a fresh-context LLM call (no conversation history) to judge completeness.
This avoids confirmation bias from the agent's own reasoning.

Enhancements:
- VerificationResult dataclass with confidence score (0.0-1.0)
- CompletionVerifier class with stats tracking
- Fresh-context verification (no conversation history bias)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_VERIFIER_SYSTEM_PROMPT = (
    "You are a task completion verifier. Your job is to determine whether an AI assistant's "
    "response actually completes the user's original request.\n\n"
    "Respond with EXACTLY one of these verdicts:\n"
    "COMPLETE: The task is done. The response directly answers the user's request.\n"
    "INCOMPLETE: The task is not done. The response doesn't fully address the request.\n"
    "NEEDS_MORE: The response makes progress but needs additional steps.\n\n"
    "After your verdict, provide:\n"
    "- A one-line summary of what was accomplished\n"
    "- Brief feedback on what's missing or what could improve\n\n"
    "Format:\n"
    "VERDICT: COMPLETE|INCOMPLETE|NEEDS_MORE\n"
    "SUMMARY: <one line>\n"
    "FEEDBACK: <brief feedback>"
)

_JSON_VERIFIER_PROMPT = (
    "You are a task completion verifier. You will receive:\n"
    "1. The original user message (what they asked for)\n"
    "2. The assistant's final response (what was delivered)\n\n"
    "Assess whether the task was completed satisfactorily.\n"
    "Respond in JSON format:\n"
    '{"confidence": 0.0-1.0, "complete": true/false, '
    '"assessment": "brief explanation", "missing": ["list of missing items"]}\n\n'
    "Be honest. A confidence of 0.7 means there's a 30% chance something was missed."
)


@dataclass
class Verdict:
    """Verdict from the completion verifier (legacy format)."""

    complete: bool
    summary: str
    feedback: str = ""


@dataclass
class VerificationResult:
    """Structured result with confidence score (P03 enhancement)."""

    is_complete: bool
    confidence: float  # 0.0 - 1.0
    assessment: str  # Human-readable assessment
    missing: list[str]  # What's missing (if incomplete)


class CompletionVerifier:
    """Fresh-context completion verifier with confidence scoring.

    Does NOT use the conversation history. Only sees:
    1. Original user message
    2. Final agent response

    This prevents the verifier from being biased by the agent's reasoning.
    """

    def __init__(self, llm_chat: Any = None):
        self.llm_chat = llm_chat
        self._verification_count = 0
        self._total_confidence = 0.0

    def verify_sync(
        self,
        original_message: str,
        final_response: str,
        llm_chat: Any = None,
    ) -> VerificationResult:
        """Synchronous verification using heuristic analysis.

        Used when no LLM is available or for fast-path checks.
        """
        if not final_response:
            return VerificationResult(
                is_complete=False,
                confidence=0.0,
                assessment="No response provided",
                missing=["No response"],
            )

        # Heuristic checks
        lower = final_response.lower()
        missing: list[str] = []
        confidence = 0.8

        # Check for uncertainty indicators
        uncertainty_phrases = ["i don't know", "i'm not sure", "i cannot", "error:", "failed"]
        for phrase in uncertainty_phrases:
            if phrase in lower:
                missing.append(f"Agent expressed uncertainty: '{phrase}'")
                confidence -= 0.3

        # Check for very short responses
        if len(final_response) < 50:
            missing.append("Response is very short")
            confidence -= 0.2

        # Check for error indicators
        error_phrases = ["exception", "traceback", "error occurred", "not implemented"]
        for phrase in error_phrases:
            if phrase in lower:
                missing.append(f"Error indicator: '{phrase}'")
                confidence -= 0.2

        confidence = max(0.0, min(1.0, confidence))
        is_complete = confidence >= 0.5 and not missing

        self._verification_count += 1
        self._total_confidence += confidence

        return VerificationResult(
            is_complete=is_complete,
            confidence=confidence,
            assessment="Heuristic verification" + (" — issues found" if missing else " — passed"),
            missing=missing,
        )

    async def verify(
        self,
        original_message: str,
        conversation: list[dict],
        llm_chat: Any = None,
        model: str = "default",
    ) -> VerificationResult:
        """Verify task completion with fresh context (async).

        Args:
            original_message: The user's original request
            conversation: Full conversation (used only to extract final response)
            llm_chat: LLM chat function
            model: Model to use for verification

        Returns:
            VerificationResult with confidence and assessment
        """
        chat_fn = llm_chat or self.llm_chat
        if not chat_fn:
            return self.verify_sync(
                original_message=original_message,
                final_response=self._extract_final_response(conversation),
            )

        final_response = self._extract_final_response(conversation)

        if not final_response:
            return VerificationResult(
                is_complete=False,
                confidence=0.0,
                assessment="No assistant response found",
                missing=["No response"],
            )

        try:
            from backend.app.services.intelligence.llm.provider import LLMMessage

            prompt = (
                f"{_JSON_VERIFIER_PROMPT}\n\n"
                f"--- USER MESSAGE ---\n{original_message}\n\n"
                f"--- ASSISTANT RESPONSE ---\n{final_response[:2000]}"
            )
            response = await chat_fn(
                messages=[LLMMessage(role="user", content=prompt)],
                model=model,
                max_tokens=300,
            )

            content = response.content.strip() if hasattr(response, "content") else str(response)

            result = json.loads(content)

            self._verification_count += 1
            self._total_confidence += result.get("confidence", 0.5)

            return VerificationResult(
                is_complete=result.get("complete", False),
                confidence=result.get("confidence", 0.5),
                assessment=result.get("assessment", ""),
                missing=result.get("missing", []),
            )

        except Exception as e:
            logger.error("Verification failed: %s", e)
            return self.verify_sync(
                original_message=original_message,
                final_response=final_response,
            )

    def _extract_final_response(self, conversation: list[dict]) -> str:
        """Extract the final assistant response from conversation history."""
        for msg in reversed(conversation):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]
        return ""

    def get_stats(self) -> dict:
        """Return verification statistics."""
        return {
            "verification_count": self._verification_count,
            "average_confidence": (
                self._total_confidence / self._verification_count
                if self._verification_count > 0
                else 0.0
            ),
        }


# ── Legacy async function (backward compatible) ────────────────────────


async def verify_completion(
    original_message: str,
    conversation_history: list[dict[str, str]],
    final_response: str,
    llm_chat: Any = None,
) -> Verdict:
    """Check whether the agent's response completes the user's request.

    Args:
        original_message: The user's original request.
        conversation_history: Full history of the conversation.
        final_response: The agent's final response to evaluate.
        llm_chat: Async chat function (e.g., llm_manager.chat). If None, returns
                  a simple heuristic-based verdict.

    Returns:
        A Verdict with completeness judgment.
    """
    if llm_chat is None:
        return _heuristic_verdict(final_response)

    try:
        from backend.app.services.intelligence.llm.provider import LLMMessage

        # Build a concise context for the verifier (no agent conversation history)
        messages = [
            LLMMessage(role="system", content=_VERIFIER_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=(
                    f"Original user request: {original_message}\n\n"
                    f"Agent's final response:\n{final_response}\n\n"
                    f"Is this complete?"
                ),
            ),
        ]

        response = await llm_chat(messages=messages, max_tokens=256)
        verdict_text = response.content.strip()
        return _parse_verdict(verdict_text)

    except Exception as exc:
        logger.warning("Completion verification LLM call failed: %s", exc)
        return _heuristic_verdict(final_response)


def _parse_verdict(text: str) -> Verdict:
    """Parse the LLM's verdict response into a structured Verdict."""
    lines = text.split("\n")
    raw_verdict = ""
    summary = ""
    feedback = ""

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("VERDICT:"):
            raw_verdict = stripped.split(":", 1)[1].strip().upper()
        elif stripped.upper().startswith("SUMMARY:"):
            summary = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("FEEDBACK:"):
            feedback = stripped.split(":", 1)[1].strip()

    complete = raw_verdict == "COMPLETE"
    return Verdict(complete=complete, summary=summary, feedback=feedback)


def _heuristic_verdict(response: str) -> Verdict:
    """Fallback heuristic when no LLM is available for verification."""
    if not response:
        return Verdict(complete=False, summary="", feedback="Empty response")

    # Ask for feedback or error indicators suggest incompleteness
    lower = response.lower()
    if any(phrase in lower for phrase in ["i don't know", "i'm not sure", "i cannot", "error:", "failed"]):
        return Verdict(
            complete=False,
            summary="Response contains uncertainty or error indicators",
            feedback="The agent expressed uncertainty or encountered an error",
        )

    # Very short responses may be incomplete
    if len(response) < 50:
        return Verdict(
            complete=False,
            summary="Response is very short",
            feedback="Consider asking for more detail",
        )

    # Default: assume complete if no red flags
    return Verdict(
        complete=True,
        summary="Response appears complete",
        feedback="",
    )
