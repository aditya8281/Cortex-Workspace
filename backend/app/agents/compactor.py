"""Context compactor — summarizes conversation history to stay within token budget.

Triggered when token count exceeds 85% of the model's context window.
Uses an LLM call (ideally a cheaper/faster model) to produce a structured
summary: Goal, Done, State, Pending.

Enhancements (P03):
- ContextCompactor class with stats tracking
- CompactionResult dataclass with structured output
- should_compact() check based on token count vs max_tokens
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CompactionResult:
    """Structured result of a compaction operation."""

    summary: str
    tokens_before: int
    tokens_after: int
    reduction_ratio: float  # (before - after) / before
    sections: dict[str, str]  # Parsed GOAL/DONE/STATE/PENDING

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
        from backend.app.services.intelligence.llm.provider import LLMMessage

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
    """Estimate token count for a list of messages.

    Uses tiktoken when available, falling back to character-based
    estimation for environments without the optional dependency.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        approx_chars_per_token: Fallback ratio (only used when tiktoken
            is unavailable).

    Returns:
        Estimated total token count.
    """
    from backend.app.agents.token_counter import count_message_tokens

    return count_message_tokens(messages, approx_chars_per_token=approx_chars_per_token)


class ContextCompactor:
    """Stateful context compactor with stats tracking.

    Wraps the module-level functions with state: threshold, max_tokens,
    and compaction metrics.
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        threshold: float = 0.85,
    ):
        self.max_tokens = max_tokens
        self.threshold = threshold
        self._compaction_count = 0
        self._total_tokens_saved = 0

    def should_compact(self, messages: list[dict[str, str]]) -> bool:
        """Check if compaction is needed based on token count vs threshold."""
        token_count = estimate_token_count(messages)
        return (token_count / self.max_tokens) >= self.threshold

    def compact_sync(self, messages: list[dict[str, str]]) -> CompactionResult:
        """Synchronous compaction using fallback (no LLM).

        Returns CompactionResult with structured output.
        """
        tokens_before = estimate_token_count(messages)
        summary = _fallback_compact(messages)
        tokens_after = estimate_token_count([{"role": "system", "content": summary}])

        reduction = 0.0
        if tokens_before > 0:
            reduction = (tokens_before - tokens_after) / tokens_before

        self._compaction_count += 1
        self._total_tokens_saved += max(0, tokens_before - tokens_after)

        return CompactionResult(
            summary=summary,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            reduction_ratio=reduction,
            sections=self._parse_sections(summary),
        )

    def _parse_sections(self, summary: str) -> dict[str, str]:
        """Parse Goal/Done/State/Pending sections from summary."""
        sections: dict[str, str] = {"goal": "", "done": "", "state": "", "pending": ""}
        current_section: str | None = None

        for line in summary.split("\n"):
            line_upper = line.upper().strip()
            if line_upper.startswith("GOAL:"):
                current_section = "goal"
                sections["goal"] = line.split(":", 1)[1].strip()
            elif line_upper.startswith("DONE:"):
                current_section = "done"
                sections["done"] = line.split(":", 1)[1].strip()
            elif line_upper.startswith("STATE:"):
                current_section = "state"
                sections["state"] = line.split(":", 1)[1].strip()
            elif line_upper.startswith("PENDING:"):
                current_section = "pending"
                sections["pending"] = line.split(":", 1)[1].strip()
            elif current_section and line.strip():
                sections[current_section] += " " + line.strip()

        return sections

    def get_stats(self) -> dict:
        """Return compaction statistics."""
        return {
            "compaction_count": self._compaction_count,
            "total_tokens_saved": self._total_tokens_saved,
            "threshold": self.threshold,
        }

    def _format_history(self, messages: list[dict[str, str]]) -> str:
        """Format message history as text."""
        return _format_history(messages)
