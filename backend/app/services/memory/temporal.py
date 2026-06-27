"""Temporal scoring — time-aware relevance ranking for memories."""

from __future__ import annotations

import math
from datetime import datetime


class TemporalScoring:
    """Time-aware relevance scoring for memories."""

    RECENCY_HALF_LIFE = 30.0
    ACCESS_HALF_LIFE = 7.0

    @staticmethod
    def recency_score(
        created_at: datetime,
        last_accessed: datetime | None = None,
        half_life: float = 30.0,
    ) -> float:
        """Calculate recency score using exponential decay."""
        now = datetime.utcnow()

        if last_accessed:
            days_since_created = max(0.0, (now - created_at).total_seconds() / 86400.0)
            days_since_access = max(0.0, (now - last_accessed).total_seconds() / 86400.0)

            creation_decay = math.exp(-0.693 * days_since_created / half_life)
            access_decay = math.exp(-0.693 * days_since_access / (half_life * 0.5))

            return 0.4 * creation_decay + 0.6 * access_decay
        else:
            days_since_created = max(0.0, (now - created_at).total_seconds() / 86400.0)
            return math.exp(-0.693 * days_since_created / half_life)

    @staticmethod
    def importance_weight(importance: float, confidence: float) -> float:
        """Calculate importance weight: importance * confidence."""
        return max(0.0, min(1.0, importance * confidence))

    @staticmethod
    def access_frequency_weight(access_count: int) -> float:
        """Calculate access frequency weight using logarithmic scaling."""
        if access_count <= 0:
            return 0.0
        return min(1.0, math.log(access_count + 1) / 10.0)

    @staticmethod
    def time_of_day_similarity(dt1: datetime, dt2: datetime) -> float:
        """Calculate similarity between two times of day."""
        hour_diff = abs(dt1.hour - dt2.hour)
        if hour_diff > 12:
            hour_diff = 24 - hour_diff
        return 1.0 - (hour_diff / 12.0)

    @staticmethod
    def day_of_week_similarity(dt1: datetime, dt2: datetime) -> float:
        """Calculate similarity between two days of the week."""
        day_diff = abs(dt1.weekday() - dt2.weekday())
        if day_diff > 3:
            day_diff = 7 - day_diff
        return max(0.0, 1.0 - (day_diff / 3.0))

    @staticmethod
    def composite_temporal_score(
        created_at: datetime,
        last_accessed: datetime | None,
        importance: float,
        confidence: float,
        access_count: int,
        reference_time: datetime | None = None,
    ) -> float:
        """Calculate a composite temporal score."""
        recency = TemporalScoring.recency_score(created_at, last_accessed)
        importance_w = TemporalScoring.importance_weight(importance, confidence)
        access_w = TemporalScoring.access_frequency_weight(access_count)

        score = 0.4 * recency + 0.35 * importance_w + 0.25 * access_w

        if reference_time:
            tod_similarity = TemporalScoring.time_of_day_similarity(
                created_at, reference_time
            )
            score = 0.85 * score + 0.15 * tod_similarity

        return max(0.0, min(1.0, score))
