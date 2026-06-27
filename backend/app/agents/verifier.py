"""Completion verifier — checks whether the agent's response actually completes the task.

Uses a fresh-context LLM call (no conversation history) to judge completeness.
This avoids confirmation bias from the agent's own reasoning.
"""

from __future__ import annotations

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


@dataclass
class Verdict:
    """Verdict from the completion verifier."""

    complete: bool
    summary: str
    feedback: str = ""


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
