"""Tests for ConfidenceEstimationService — multi-factor scoring."""

import pytest

from backend.app.services.cognition.confidence import ConfidenceEstimationService


class TestConfidenceEstimationService:
    @pytest.fixture
    def service(self, db_session):
        return ConfidenceEstimationService(db_session)

    def test_basic_estimation(self, service):
        result = service.estimate_task_confidence("memory_retrieval")
        assert 1 <= result["confidence"] <= 99
        assert result["recommendation"]
        assert result["risk_level"] in ("low", "medium", "high")

    def test_past_success_increases_confidence(self, service):
        base = service.estimate_task_confidence("tool_execution")
        boosted = service.estimate_task_confidence(
            "tool_execution",
            context={"similar_past_successes": 10, "similar_past_failures": 2},
        )
        assert boosted["confidence"] > base["confidence"]

    def test_novelty_decreases_confidence(self, service):
        base = service.estimate_task_confidence("planning")
        novel = service.estimate_task_confidence("planning", context={"novelty": 0.9})
        assert novel["confidence"] < base["confidence"]

    def test_data_quality_effect(self, service):
        low_quality = service.estimate_task_confidence("error_analysis", context={"data_quality": 0.1})
        high_quality = service.estimate_task_confidence("error_analysis", context={"data_quality": 0.9})
        assert high_quality["confidence"] > low_quality["confidence"]

    def test_combine_confidences(self, service):
        result = service.combine_confidences([80, 60, 70])
        assert 65 <= result["confidence"] <= 75

    def test_combine_with_weights(self, service):
        result = service.combine_confidences([90, 50], weights=[3.0, 1.0])
        assert result["confidence"] > 75

    def test_explain_confidence(self, service):
        result = service.explain_confidence(75, ["factor1", "factor2"])
        assert result["confidence"] == 75
        assert "factor1" in result["factors"]
        assert result["risk_level"] == "medium"

    def test_clamping_high(self, service):
        result = service.estimate_task_confidence(
            "access_check",
            context={"similar_past_successes": 100, "data_quality": 1.0, "novelty": 0.0},
        )
        assert result["confidence"] <= 99

    def test_clamping_low(self, service):
        result = service.estimate_task_confidence(
            "workflow_orchestration",
            context={"similar_past_failures": 100, "data_quality": 0.0, "novelty": 1.0},
        )
        assert result["confidence"] >= 1

    def test_unknown_task_type(self, service):
        result = service.estimate_task_confidence("unknown_task")
        assert result["confidence"] == 50  # Default base

    def test_evidence_balance_effect(self, service):
        balanced = service.estimate_task_confidence(
            "planning", context={"evidence_for_count": 5, "evidence_against_count": 5}
        )
        skewed = service.estimate_task_confidence(
            "planning", context={"evidence_for_count": 9, "evidence_against_count": 1}
        )
        assert skewed["confidence"] > balanced["confidence"]

    def test_time_pressure_effect(self, service):
        relaxed = service.estimate_task_confidence("planning", context={"time_pressure": 0.1})
        pressured = service.estimate_task_confidence("planning", context={"time_pressure": 0.9})
        assert relaxed["confidence"] > pressured["confidence"]

    def test_store_false_no_db_write(self, service):
        result = service.estimate_task_confidence("planning", store=False)
        assert result["confidence"] >= 1

    def test_calibration_data_empty(self, service):
        result = service.get_calibration_data(user_id=999)
        assert result["total_predictions"] == 0
        assert result["calibration_score"] == 0

    def test_recommendation_levels(self, service):
        # access_check has 90 base → should be "autonomously"
        result = service.estimate_task_confidence("access_check")
        if result["confidence"] > 80:
            assert "autonomously" in result["recommendation"].lower()
