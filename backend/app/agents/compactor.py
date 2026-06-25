"""Context compactor — summarizes conversation history to stay within token budget.

Triggered when token count exceeds 85% of the model's context window.
Uses an LLM call (ideally a cheaper/faster model) to produce a structured
summary: Goal, Done, State, Pending.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default compaction prompt — instructs the LLM to produce a structured summary
_COMPACTION_PROMPT = (
    "You are a context compaction assistant. Your job is to summarize the following "
    "conversation between a user and an AI assistant. Produce a concise, structured summary "
    "with these sections:\n\n"
    "GOAL: What the user originally wanted\n"
    "DONE: What has been accomplished so far\n"
    "STATE: Current state of the task\n"
    "PENDING: What remains to be done\n\n"
    "Be concise. Preserve all important facts, file paths, errors, and decisions. "
    "Drop pleasantries and redundant exchanges."
)


async def compact_context(
    history: list[dict[str, str]],
    llm_chat: Any = None,
    model: str | None = None,
) -> str:
    """Compact conversation history into a structured summary.

    Args:
        history: List of message dicts with 'role' and 'content' keys.
        llm_chat: Callable async function for LLM chat (e.g., llm_manager.chat).
                  If None, returns a simple token-count-based summary as fallback.
        model: Optional model name override for the compaction call.

    Returns:
        A structured summary string (Goal / Done / State / Pending format).
    """
    if not history:
        return ""

    # If no LLM available, do a simple fallback summary
    if llm_chat is None:
        return _fallback_compact(history)

    try:
        # Build the compaction request
        history_text = _format_history(history)
        user_prompt = f"Summarize this conversation:\n\n{history_text}"

        # Import LLMMessage locally to avoid circular imports
        from backend.app.services.llm.provider import LLMMessage

        messages = [
            LLMMessage(role="system", content=_COMPACTION_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await llm_chat(
            messages=messages,
            model=model,
            max_tokens=1024,
        )

        # llm_chat returns LLMResponse with .content
        summary = response.content.strip()
        if summary:
            logger.info("Context compacted: %d chars → %d chars", len(history_text), len(summary))
            return summary

    except Exception as exc:
        logger.warning("Context compaction LLM call failed: %s", exc)

    # Fallback on any error
    return _fallback_compact(history)


def _fallback_compact(history: list[dict[str, str]]) -> str:
    """Simple fallback: just note how many messages and when the oldest is."""
    if not history:
        return ""

    user_msgs = sum(1 for m in history if m.get("role") == "user")
    asst_msgs = sum(1 for m in history if m.get("role") == "assistant")
    tool_msgs = sum(1 for m in history if m.get("role") == "tool")

    first_content = history[0].get("content", "")[:200] if history else ""
    last_content = history[-1].get("content", "")[:200] if history else ""

    return (
        f"GOAL: (from compaction) Original request: {first_content}\n"
        f"DONE: {asst_msgs} assistant responses, {tool_msgs} tool calls\n"
        f"STATE: {user_msgs} user messages, {asst_msgs} assistant messages across {len(history)} turns\n"
        f"PENDING: Last output: {last_content}\n"
    )


def _format_history(history: list[dict[str, str]]) -> str:
    """Format message history as text for the compaction LLM prompt."""
    lines: list[str] = []
    for msg in history:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}]\n{content}\n")
    return "\n".join(lines)


def estimate_token_count(
    messages: list[dict[str, str]],
    approx_chars_per_token: float = 4.0,
) -> int:
    """Rough token count estimate (character-based, for compaction decisions).

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        approx_chars_per_token: Rough ratio (4.0 for English text).

    Returns:
        Estimated total token count.
    """
    total_chars = sum(len(m.get("content", "")) for m in messages)
    # Add overhead for role markers, formatting, etc.
    total_chars += len(messages) * 10
    return int(total_chars / approx_chars_per_token)
