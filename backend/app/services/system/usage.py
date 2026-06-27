"""Model usage analytics tracking."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.models.intelligence.model_catalog import ModelUsage

logger = logging.getLogger(__name__)


class UsageTracker:
    """Track model usage for analytics and recommendations."""

    def __init__(self, db: Session):
        self.db = db

    def record_usage(
        self,
        model_name: str,
        usage_type: str = "chat",
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        duration_ms: float = 0,
        context_length: int = 0,
        user_id: int | None = None,
    ):
        """Record a model usage event."""
        try:
            tps = (tokens_completion / (duration_ms / 1000)) if duration_ms > 0 else 0
            prompt_tps = (tokens_prompt / (duration_ms / 1000)) if duration_ms > 0 and tokens_prompt > 0 else 0

            usage = ModelUsage(
                model_variant_id=None,
                user_id=user_id,
                usage_type=usage_type,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
                duration_ms=duration_ms,
                tps_generation=tps,
                tps_prompt=prompt_tps,
                context_length=context_length,
            )
            self.db.add(usage)
            self.db.commit()
        except Exception as e:
            logger.warning("Failed to record usage: %s", e)

    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        from sqlalchemy import func, select

        total = self.db.execute(select(func.count(ModelUsage.id))).scalar() or 0
        avg_tps = self.db.execute(select(func.avg(ModelUsage.tps_generation))).scalar() or 0
        total_tokens = (
            self.db.execute(select(func.sum(ModelUsage.tokens_prompt + ModelUsage.tokens_completion))).scalar() or 0
        )

        return {
            "total_requests": total,
            "avg_tps_generation": round(float(avg_tps), 1),
            "total_tokens": int(total_tokens),
        }
