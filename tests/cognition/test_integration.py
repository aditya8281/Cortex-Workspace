"""Cross-domain integration tests — cognition + execution services working together."""

import pytest

from backend.app.services.cognition.confidence import ConfidenceEstimationService
from backend.app.services.cognition.error_analysis import ErrorAnalysisService
from backend.app.services.cognition.hypothesis import HypothesisService
from backend.app.services.cognition.planning import TaskPlanningService


class TestPlanToErrorToHypothesisFlow:
    """Integration: plan step fails → error analysis → hypothesis about root cause."""

    @pytest.mark.asyncio
    async def test_full_flow(self, db_session):
        # 1. Create a plan
        planning = TaskPlanningService(db_session)
        plan = planning.create_plan(user_id=1, goal="Fix authentication bug")
        assert plan.status == "active"
        assert len(plan.steps) > 0

        # 2. Execute first step — it fails
        plan = planning.execute_step(plan.id, 0, error="Token validation failed")
        assert plan.steps[0]["status"] == "failed"

        # 3. Analyze the error
        error_svc = ErrorAnalysisService(db_session)
        analysis = error_svc.analyze_error(
            user_id=1,
            error_type="AuthenticationError",
            error_message="Token validation failed during execution",
            context={"plan_id": plan.id, "step": 0},
        )
        assert analysis.fingerprint is not None

        # 4. Generate hypothesis about root cause
        hypo_svc = HypothesisService(db_session)
        hypo = hypo_svc.generate_hypothesis(
            user_id=1,
            hypothesis="The bug is in the token validation middleware",
            source="error_analysis",
            related_plan_id=plan.id,
        )
        assert hypo.status == "active"
        assert hypo.confidence == 0.5  # Prior with no evidence

        # 5. Add evidence
        hypo = hypo_svc.add_evidence(hypo.id, "Token expires too early", supports=True, weight=0.8)
        assert len(hypo.evidence_for) == 1
        assert hypo.confidence > 0.5

        # 6. Estimate confidence for fixing
        conf_svc = ConfidenceEstimationService(db_session)
        result = conf_svc.estimate_task_confidence(
            "error_analysis",
            context={"user_id": 1, "source": "plan_error"},
        )
        assert result["confidence"] > 0
        assert "recommendation" in result


class TestHypothesisResolutionFlow:
    """Integration: generate → add evidence → resolve → verify state."""

    def test_confirm_with_evidence(self, db_session):
        svc = HypothesisService(db_session)

        # Create hypothesis with strong supporting evidence
        hypo = svc.generate_hypothesis(
            user_id=1,
            hypothesis="The API rate limiter is too strict",
            evidence_for=[
                {"text": "Users report 429 errors frequently", "weight": 0.9},
                {"text": "Rate limit logs show high rejection rate", "weight": 0.8},
            ],
        )

        # Should have high confidence from initial evidence
        assert hypo.confidence > 0.5

        # Resolve as confirmed
        resolved = svc.resolve_hypothesis(hypo.id, "confirmed", "Confirmed by user testing")
        assert resolved.status == "confirmed"
        assert resolved.resolved_at is not None
        assert resolved.resolution_reason == "Confirmed by user testing"

        # Verify not in active list
        active = svc.get_active_hypotheses(1)
        assert all(h.id != hypo.id for h in active)

    def test_reject_with_contradicting_evidence(self, db_session):
        svc = HypothesisService(db_session)

        hypo = svc.generate_hypothesis(
            user_id=1,
            hypothesis="The database is overloaded",
        )

        # Add contradicting evidence — weight 0.9 then 5× weight 0.8
        # Prior odds=1.0, confidence=0.5. After 6 contradicting entries:
        # Each divides odds by (1+weight). 4+ entries cross the 0.10 threshold.
        hypo = svc.add_evidence(hypo.id, "DB response times are normal", supports=False, weight=0.9)
        assert hypo.confidence < 0.5

        # Keep adding contradicting evidence until auto-reject fires
        for _ in range(5):
            if hypo.status == "rejected":
                break
            hypo = svc.add_evidence(hypo.id, "No DB performance issues found", supports=False, weight=0.8)

        # Verify auto-reject fired (confidence ≤ 0.10 → status "rejected")
        fetched = svc.get_hypothesis(hypo.id)
        assert fetched.status == "rejected", (
            f"Expected rejected, got {fetched.status} at confidence={fetched.confidence}"
        )


class TestErrorPatternDetection:
    """Integration: multiple errors → pattern detection → severity classification."""

    def test_pattern_across_errors(self, db_session):
        svc = ErrorAnalysisService(db_session)

        # Create errors of same type
        for i in range(4):
            svc.analyze_error(1, "ValueError", f"Input parsing error {i}", {"module": "parser"})

        # Create different type
        svc.analyze_error(1, "TypeError", "Type mismatch in function", {})

        # Get patterns — returns list of dicts sorted by count desc
        patterns = svc.get_error_patterns(1)
        assert isinstance(patterns, list)
        assert len(patterns) >= 1
        assert patterns[0]["count"] >= 1

    def test_severity_classification(self, db_session):
        svc = ErrorAnalysisService(db_session)

        # Critical errors
        r1 = svc.analyze_error(1, "SecurityError", "Unauthorized access", {})
        r2 = svc.analyze_error(1, "EncryptionError", "Encryption failure", {})

        # Error-level errors
        r3 = svc.analyze_error(1, "ValueError", "Invalid input", {})

        # Warning-level errors
        r4 = svc.analyze_error(1, "DeprecationWarning", "Old API used", {})

        # Security errors should be higher severity
        assert r1.severity == "critical"
        assert r2.severity == "critical"
        assert r3.severity == "error"
        assert r4.severity == "warning"


class TestConfidenceWithHistory:
    """Integration: confidence estimation with context affecting factors."""

    def test_novel_task_vs_familiar(self, db_session):
        svc = ConfidenceEstimationService(db_session)

        # Novel task (no history)
        novel = svc.estimate_task_confidence(
            "planning",
            context={"user_id": 999},
            store=False,
        )

        # After repeated successes — familiarity should boost confidence
        familiar = svc.estimate_task_confidence(
            "planning",
            context={"user_id": 999, "historical_success_rate": 0.95},
            store=False,
        )

        assert familiar["confidence"] >= novel["confidence"]

    def test_combine_multiple_sources(self, db_session):
        svc = ConfidenceEstimationService(db_session)

        result = svc.combine_confidences([70, 80, 60], [0.5, 0.3, 0.2])
        assert 1 <= result["confidence"] <= 99
        assert len(result["input_weights"]) == 3

    def test_empty_calibration(self, db_session):
        svc = ConfidenceEstimationService(db_session)
        data = svc.get_calibration_data(999)
        assert data["total_predictions"] == 0
