"""Multi-factor confidence estimation for Cortex reasoning outputs.

Estimates confidence 1-99 based on task type base rate, historical success,
novelty, data quality, evidence balance, and time pressure.
Tracks calibration: how well do confidence scores predict actual outcomes?
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.cognition.confidence_score import ConfidenceScore


class ConfidenceEstimationService:
    """Multi-factor confidence estimation with calibration tracking."""

    TASK_BASE_CONFIDENCE: dict[str, int] = {
        "memory_retrieval": 70,
        "file_analysis": 80,
        "code_generation": 60,
        "planning": 50,
        "error_analysis": 65,
        "hypothesis_generation": 55,
        "workflow_orchestration": 45,
        "tool_execution": 75,
        "data_export": 85,
        "access_check": 90,
    }

    HIGH_CONFIDENCE_THRESHOLD = 80
    MEDIUM_CONFIDENCE_THRESHOLD = 60
    LOW_CONFIDENCE_THRESHOLD = 40

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def estimate_task_confidence(
        self,
        task_type: str,
        context: dict[str, Any] | None = None,
        store: bool = True,
    ) -> dict[str, Any]:
        context = context or {}

        confidence = self.TASK_BASE_CONFIDENCE.get(task_type, 50)
        factors_applied: list[str] = []

        # Historical success adjustment
        past_successes = context.get("similar_past_successes", 0)
        past_failures = context.get("similar_past_failures", 0)
        if past_successes + past_failures > 0:
            success_rate = past_successes / (past_successes + past_failures)
            adjustment = int((success_rate - 0.5) * 20)
            confidence += adjustment
            factors_applied.append(f"historical_success_rate={success_rate:.2f} (adj={adjustment:+d})")

        # Novelty adjustment
        novelty = context.get("novelty", 0.0)
        if novelty > 0.8:
            confidence -= 20
            factors_applied.append(f"high_novelty={novelty:.2f} (adj=-20)")
        elif novelty > 0.5:
            confidence -= 10
            factors_applied.append(f"medium_novelty={novelty:.2f} (adj=-10)")
        elif novelty > 0.2:
            confidence -= 5
            factors_applied.append(f"low_novelty={novelty:.2f} (adj=-5)")

        # Data quality adjustment
        data_quality = context.get("data_quality", 0.5)
        if data_quality > 0.8:
            confidence += 10
            factors_applied.append(f"high_data_quality={data_quality:.2f} (adj=+10)")
        elif data_quality < 0.3:
            confidence -= 15
            factors_applied.append(f"low_data_quality={data_quality:.2f} (adj=-15)")

        # Evidence balance
        evidence_for = context.get("evidence_for_count", 0)
        evidence_against = context.get("evidence_against_count", 0)
        total_evidence = evidence_for + evidence_against
        if total_evidence > 0:
            balance = evidence_for / total_evidence
            evidence_adjustment = int((balance - 0.5) * 15)
            confidence += evidence_adjustment
            factors_applied.append(f"evidence_balance={balance:.2f} (adj={evidence_adjustment:+d})")

        # Time pressure
        time_pressure = context.get("time_pressure", 0.5)
        if time_pressure < 0.3:
            confidence += 5
            factors_applied.append("low_time_pressure (adj=+5)")
        elif time_pressure > 0.8:
            confidence -= 10
            factors_applied.append("high_time_pressure (adj=-10)")

        confidence = max(1, min(99, confidence))

        recommendation = self._generate_recommendation(confidence)
        risk_level = self._assess_risk_level(confidence)

        result: dict[str, Any] = {
            "task_type": task_type,
            "confidence": confidence,
            "recommendation": recommendation,
            "risk_level": risk_level,
            "factors": factors_applied,
        }

        if store and self.db:
            score = ConfidenceScore(
                user_id=context.get("user_id", 0),
                task_type=task_type,
                confidence=confidence / 100.0,
                factors=[{"factor": f} for f in factors_applied],
                context=context,
                source=context.get("source", "estimation"),
                related_id=context.get("related_id"),
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(score)
            self.db.commit()

        return result

    def explain_confidence(self, confidence: int, factors: list[str]) -> dict[str, Any]:
        recommendation = self._generate_recommendation(confidence)
        risk_level = self._assess_risk_level(confidence)

        explanation_parts: list[str] = []
        if confidence > 80:
            explanation_parts.append("Confidence is high based on:")
        elif confidence > 60:
            explanation_parts.append("Confidence is moderate based on:")
        else:
            explanation_parts.append("Confidence is low based on:")

        for factor in factors:
            explanation_parts.append(f"  - {factor}")

        return {
            "confidence": confidence,
            "explanation": "\n".join(explanation_parts),
            "factors": factors,
            "recommendation": recommendation,
            "risk_level": risk_level,
        }

    def combine_confidences(
        self,
        confidences: list[int],
        weights: list[float] | None = None,
    ) -> dict[str, Any]:
        if not confidences:
            return {"confidence": 50, "method": "default", "factors": []}

        if weights is None:
            weights = [1.0] * len(confidences)

        weighted_sum = sum(c * w for c, w in zip(confidences, weights, strict=True))
        total_weight = sum(weights)

        combined = int(weighted_sum / total_weight) if total_weight > 0 else 50

        return {
            "confidence": combined,
            "method": "weighted_average",
            "input_scores": confidences,
            "input_weights": weights,
            "factors": [
                f"input_{i}: {c} (weight={w})" for i, (c, w) in enumerate(zip(confidences, weights, strict=True))
            ],
        }

    def get_calibration_data(
        self,
        user_id: int,
        task_type: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        if not self.db:
            return {"error": "Database not available"}

        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = self.db.query(ConfidenceScore).filter(
            ConfidenceScore.user_id == user_id,
            ConfidenceScore.created_at >= since,
        )
        if task_type:
            query = query.filter(ConfidenceScore.task_type == task_type)

        scores = query.all()
        total = len(scores)
        calibrated = sum(1 for s in scores if s.was_accurate == 1)

        by_type: dict[str, list[ConfidenceScore]] = {}
        for score in scores:
            by_type.setdefault(score.task_type, []).append(score)

        type_calibration: dict[str, dict[str, Any]] = {}
        for tt, type_scores in by_type.items():
            type_total = len(type_scores)
            type_calibrated = sum(1 for s in type_scores if s.was_accurate == 1)
            type_calibration[tt] = {
                "total": type_total,
                "calibrated": type_calibrated,
                "score": (type_calibrated / type_total * 100) if type_total > 0 else 0,
            }

        return {
            "total_predictions": total,
            "calibrated_count": calibrated,
            "calibration_score": (calibrated / total * 100) if total > 0 else 0,
            "by_task_type": type_calibration,
        }

    def retroactive_calibration(self, score_id: int, actual_outcome: str) -> ConfidenceScore:
        if not self.db:
            raise ValueError("Database required for calibration")

        score = self.db.query(ConfidenceScore).filter(ConfidenceScore.id == score_id).first()
        if not score:
            raise ValueError(f"Confidence score {score_id} not found")

        score.actual_outcome = actual_outcome
        predicted_positive = score.confidence > 0.5
        actual_positive = actual_outcome == "success"
        score.was_accurate = 1 if predicted_positive == actual_positive else 0

        self.db.commit()
        self.db.refresh(score)
        return score

    def _generate_recommendation(self, confidence: int) -> str:
        if confidence > self.HIGH_CONFIDENCE_THRESHOLD:
            return "Proceed autonomously. Confidence is high enough for automated action."
        elif confidence > self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "Proceed with verification. Consider confirming critical decisions with user."
        elif confidence > self.LOW_CONFIDENCE_THRESHOLD:
            return "Request user confirmation before proceeding. Confidence is moderate."
        else:
            return "Gather more information before acting. Seek user input or additional evidence."

    def _assess_risk_level(self, confidence: int) -> str:
        if confidence > 75:
            return "low"
        elif confidence > 45:
            return "medium"
        else:
            return "high"
