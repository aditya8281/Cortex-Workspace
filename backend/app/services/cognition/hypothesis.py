"""Hypothesis generation and management with Bayesian confidence updating.

Lifecycle:
1. Generate hypothesis (status: active, confidence: 0.5)
2. Add supporting/contradicting evidence (confidence updates)
3. Resolve: confirm (confidence > 0.90) or reject (confidence < 0.10)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.cognition.hypothesis import Hypothesis


class HypothesisService:
    """Hypothesis generation and Bayesian confidence management."""

    PRIOR_STRENGTH = 2.0
    AUTO_CONFIRM_THRESHOLD = 0.90
    AUTO_REJECT_THRESHOLD = 0.10

    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_hypothesis(
        self,
        user_id: int,
        hypothesis: str,
        evidence_for: list[dict[str, Any]] | None = None,
        evidence_against: list[dict[str, Any]] | None = None,
        source: str | None = None,
        related_plan_id: int | None = None,
        related_hypothesis_id: int | None = None,
    ) -> Hypothesis:
        ev_for = evidence_for or []
        ev_against = evidence_against or []
        confidence = self._calculate_confidence(ev_for, ev_against)

        hypo = Hypothesis(
            user_id=user_id,
            hypothesis=hypothesis,
            evidence_for=ev_for,
            evidence_against=ev_against,
            confidence=confidence,
            confidence_history=[
                {
                    "value": confidence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trigger": "creation",
                    "evidence_count": len(ev_for) + len(ev_against),
                }
            ],
            status="active",
            source=source,
            related_plan_id=related_plan_id,
            related_hypothesis_id=related_hypothesis_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(hypo)
        self.db.commit()
        self.db.refresh(hypo)
        return hypo

    def add_evidence(
        self,
        hypothesis_id: int,
        text: str,
        supports: bool,
        weight: float = 1.0,
        source: str | None = None,
    ) -> Hypothesis:
        hypo = self.db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()
        if not hypo:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")
        if hypo.status != "active":
            raise ValueError(f"Hypothesis is already {hypo.status}")

        weight = max(0.0, min(1.0, weight))
        evidence_item: dict[str, Any] = {
            "text": text,
            "weight": weight,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if supports:
            hypo.evidence_for = list(hypo.evidence_for or []) + [evidence_item]
        else:
            hypo.evidence_against = list(hypo.evidence_against or []) + [evidence_item]

        old_confidence = hypo.confidence
        new_confidence = self._calculate_confidence(hypo.evidence_for or [], hypo.evidence_against or [])
        hypo.confidence = new_confidence

        history = list(hypo.confidence_history or [])
        history.append(
            {
                "value": new_confidence,
                "previous_value": old_confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trigger": f"evidence_{'added' if supports else 'contradicted'}",
                "evidence_text": text[:100],
                "evidence_weight": weight,
            }
        )
        hypo.confidence_history = history
        hypo.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(hypo)

        self._check_auto_resolve(hypo)
        return hypo

    def resolve_hypothesis(
        self,
        hypothesis_id: int,
        status: str,
        reason: str | None = None,
    ) -> Hypothesis:
        if status not in ("confirmed", "rejected"):
            raise ValueError(f"Status must be 'confirmed' or 'rejected', got '{status}'")

        hypo = self.db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()
        if not hypo:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")
        if hypo.status != "active":
            raise ValueError(f"Hypothesis is already {hypo.status}")

        hypo.status = status
        hypo.resolved_at = datetime.now(timezone.utc)
        hypo.resolution_reason = reason
        hypo.updated_at = datetime.now(timezone.utc)

        history = list(hypo.confidence_history or [])
        history.append(
            {
                "value": hypo.confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trigger": f"resolved_{status}",
                "reason": reason,
            }
        )
        hypo.confidence_history = history

        self.db.commit()
        self.db.refresh(hypo)
        return hypo

    def get_hypothesis(self, hypothesis_id: int) -> Hypothesis | None:
        return self.db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()

    def get_user_hypotheses(
        self,
        user_id: int,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Hypothesis]:
        query = self.db.query(Hypothesis).filter(Hypothesis.user_id == user_id)
        if status:
            query = query.filter(Hypothesis.status == status)
        return query.order_by(Hypothesis.created_at.desc()).limit(limit).all()

    def get_active_hypotheses(self, user_id: int) -> list[Hypothesis]:
        return self.get_user_hypotheses(user_id, status="active")

    def get_high_confidence_hypotheses(
        self,
        user_id: int,
        threshold: float = 0.7,
    ) -> list[Hypothesis]:
        return (
            self.db.query(Hypothesis)
            .filter(
                Hypothesis.user_id == user_id,
                Hypothesis.status == "active",
                Hypothesis.confidence >= threshold,
            )
            .order_by(Hypothesis.confidence.desc())
            .all()
        )

    def merge_hypotheses(self, hypothesis_id: int, other_id: int) -> Hypothesis:
        h1 = self.db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()
        h2 = self.db.query(Hypothesis).filter(Hypothesis.id == other_id).first()

        if not h1 or not h2:
            raise ValueError("One or both hypotheses not found")
        if h1.user_id != h2.user_id:
            raise ValueError("Cannot merge hypotheses from different users")
        if h1.status != "active" or h2.status != "active":
            raise ValueError("Can only merge active hypotheses")

        combined_for = list(h1.evidence_for or []) + list(h2.evidence_for or [])
        combined_against = list(h1.evidence_against or []) + list(h2.evidence_against or [])

        h1.evidence_for = combined_for
        h1.evidence_against = combined_against
        h1.hypothesis = f"{h1.hypothesis} + {h2.hypothesis}"
        h1.confidence = self._calculate_confidence(combined_for, combined_against)
        h1.updated_at = datetime.now(timezone.utc)

        h2.status = "merged"
        h2.resolved_at = datetime.now(timezone.utc)
        h2.resolution_reason = f"Merged into hypothesis {h1.id}"

        self.db.commit()
        self.db.refresh(h1)
        return h1

    def _calculate_confidence(
        self,
        evidence_for: list[dict[str, Any]],
        evidence_against: list[dict[str, Any]],
    ) -> float:
        """Bayesian odds update.

        Prior: 0.5. Each supporting evidence multiplies odds by (1 + weight).
        Each contradicting evidence divides odds by (1 + weight).
        """
        if not evidence_for and not evidence_against:
            return 0.5

        odds = 1.0  # prior odds = 0.5 / 0.5

        for ev in evidence_for:
            weight = ev.get("weight", 1.0) if isinstance(ev, dict) else 1.0
            odds *= 1.0 + weight

        for ev in evidence_against:
            weight = ev.get("weight", 1.0) if isinstance(ev, dict) else 1.0
            odds /= 1.0 + weight

        confidence = odds / (1.0 + odds)
        return max(0.01, min(0.99, confidence))

    def _check_auto_resolve(self, hypo: Hypothesis) -> None:
        if hypo.confidence >= self.AUTO_CONFIRM_THRESHOLD:
            hypo.status = "confirmed"
            hypo.resolved_at = datetime.now(timezone.utc)
            hypo.resolution_reason = "Auto-confirmed: confidence exceeded threshold"
            self.db.commit()
        elif hypo.confidence <= self.AUTO_REJECT_THRESHOLD:
            hypo.status = "rejected"
            hypo.resolved_at = datetime.now(timezone.utc)
            hypo.resolution_reason = "Auto-rejected: confidence below threshold"
            self.db.commit()
