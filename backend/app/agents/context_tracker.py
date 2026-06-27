"""Context usage tracking — P07 Task 3.

Tracks context window usage over time and predicts compaction needs.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.agents.token_counter import TokenCounter


@dataclass
class ContextUsageSnapshot:
    """Point-in-time snapshot of context usage."""

    tokens_used: int = 0
    tokens_max: int = 0
    usage_pct: float = 0.0
    message_count: int = 0
    compaction_triggered: bool = False


COMPACTION_THRESHOLD = 0.85  # trigger compaction at 85%


class ContextTracker:
    """Track context window usage over time."""

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self._token_counter = token_counter or TokenCounter()
        self._history: list[ContextUsageSnapshot] = []
        self._current: ContextUsageSnapshot | None = None

    async def snapshot(self, messages: list[dict]) -> ContextUsageSnapshot:
        """Take a snapshot of current context usage."""
        tokens_used = await self._token_counter.count_tokens(messages)
        tokens_max = self._token_counter.max_context_tokens
        usage_pct = tokens_used / tokens_max if tokens_max > 0 else 0.0
        compaction = usage_pct >= COMPACTION_THRESHOLD

        snap = ContextUsageSnapshot(
            tokens_used=tokens_used,
            tokens_max=tokens_max,
            usage_pct=usage_pct,
            message_count=len(messages),
            compaction_triggered=compaction,
        )
        self._history.append(snap)
        self._current = snap
        return snap

    def get_current_usage(self) -> ContextUsageSnapshot | None:
        """Get the most recent snapshot."""
        return self._current

    def get_usage_history(self) -> list[ContextUsageSnapshot]:
        """Get all snapshots."""
        return list(self._history)

    def predict_compaction_turns(
        self,
        messages: list[dict],
        *,
        avg_tokens_per_turn: float = 500.0,
    ) -> int:
        """Predict how many turns until compaction is needed.

        Returns -1 if no history available.
        """
        if not self._history:
            return -1
        current = self._history[-1]
        remaining = current.tokens_max - current.tokens_used
        if remaining <= 0:
            return 0
        turns = int(remaining / avg_tokens_per_turn) if avg_tokens_per_turn > 0 else 0
        return max(0, turns)

    def get_stats(self) -> dict:
        """Get aggregate tracker stats."""
        max_usage = max((s.usage_pct for s in self._history), default=0.0)
        return {
            "current_usage_pct": self._current.usage_pct if self._current else 0.0,
            "compaction_count": sum(1 for s in self._history if s.compaction_triggered),
            "snapshots_taken": len(self._history),
            "max_usage_reached": max_usage,
        }
