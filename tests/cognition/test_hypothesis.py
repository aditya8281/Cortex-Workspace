"""Tests for HypothesisService — Bayesian confidence updating."""

import pytest

from backend.app.services.cognition.hypothesis import HypothesisService


class TestHypothesisService:
    @pytest.fixture
    def service(self, db_session):
        return HypothesisService(db_session)

    def test_generate_hypothesis(self, service):
        hypo = service.generate_hypothesis(
            user_id=1,
            hypothesis="Test hypothesis",
            evidence_for=[{"text": "support", "weight": 1.0}],
            source="error_analysis",
        )
        assert hypo.hypothesis == "Test hypothesis"
        assert hypo.confidence > 0.5  # Supporting evidence > prior
        assert hypo.status == "active"
        assert hypo.source == "error_analysis"
        assert len(hypo.confidence_history) == 1

    def test_generate_with_no_evidence(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="Bare")
        assert hypo.confidence == 0.5
        assert hypo.evidence_for == []
        assert hypo.evidence_against == []

    def test_add_supporting_evidence(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        initial_conf = hypo.confidence

        updated = service.add_evidence(hypo.id, "Supporting evidence", supports=True, weight=0.8)
        assert len(updated.evidence_for) == 1
        assert updated.confidence > initial_conf
        assert len(updated.confidence_history) == 2

    def test_add_contradicting_evidence(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        initial_conf = hypo.confidence

        updated = service.add_evidence(hypo.id, "Contradicting evidence", supports=False, weight=0.8)
        assert len(updated.evidence_against) == 1
        assert updated.confidence < initial_conf

    def test_bayesian_balanced(self, service):
        hypo = service.generate_hypothesis(
            user_id=1,
            hypothesis="Balanced",
            evidence_for=[{"text": "for", "weight": 1.0}],
            evidence_against=[{"text": "against", "weight": 1.0}],
        )
        assert 0.45 <= hypo.confidence <= 0.55

    def test_bayesian_strong_support(self, service):
        hypo = service.generate_hypothesis(
            user_id=1,
            hypothesis="Strong support",
            evidence_for=[
                {"text": "e1", "weight": 1.0},
                {"text": "e2", "weight": 1.0},
                {"text": "e3", "weight": 1.0},
            ],
        )
        assert hypo.confidence > 0.8

    def test_bayesian_weighted_evidence(self, service):
        hypo1 = service.generate_hypothesis(
            user_id=1,
            hypothesis="Low weight",
            evidence_for=[{"text": "weak", "weight": 0.2}],
        )
        hypo2 = service.generate_hypothesis(
            user_id=1,
            hypothesis="High weight",
            evidence_for=[{"text": "strong", "weight": 1.0}],
        )
        assert hypo2.confidence > hypo1.confidence

    def test_resolve_confirm(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        resolved = service.resolve_hypothesis(hypo.id, "confirmed", reason="Evidence strong")
        assert resolved.status == "confirmed"
        assert resolved.resolved_at is not None
        assert resolved.resolution_reason == "Evidence strong"

    def test_resolve_reject(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        resolved = service.resolve_hypothesis(hypo.id, "rejected")
        assert resolved.status == "rejected"

    def test_invalid_resolution(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        with pytest.raises(ValueError, match="confirmed.*rejected"):
            service.resolve_hypothesis(hypo.id, "invalid")

    def test_cannot_add_evidence_to_resolved(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        service.resolve_hypothesis(hypo.id, "confirmed")
        with pytest.raises(ValueError, match="already"):
            service.add_evidence(hypo.id, "Too late", supports=True)

    def test_merge_hypotheses(self, service):
        h1 = service.generate_hypothesis(
            user_id=1,
            hypothesis="H1",
            evidence_for=[{"text": "e1", "weight": 1.0}],
        )
        h2 = service.generate_hypothesis(
            user_id=1,
            hypothesis="H2",
            evidence_for=[{"text": "e2", "weight": 1.0}],
        )
        merged = service.merge_hypotheses(h1.id, h2.id)
        assert len(merged.evidence_for) == 2
        assert merged.status == "active"

        h2_refreshed = service.get_hypothesis(h2.id)
        assert h2_refreshed.status == "merged"

    def test_merge_different_users_fails(self, service):
        h1 = service.generate_hypothesis(user_id=1, hypothesis="H1")
        h2 = service.generate_hypothesis(user_id=2, hypothesis="H2")
        with pytest.raises(ValueError, match="different users"):
            service.merge_hypotheses(h1.id, h2.id)

    def test_get_high_confidence(self, service):
        service.generate_hypothesis(
            user_id=1,
            hypothesis="High conf",
            evidence_for=[{"text": f"e{i}", "weight": 1.0} for i in range(5)],
        )
        service.generate_hypothesis(user_id=1, hypothesis="Low conf")

        high = service.get_high_confidence_hypotheses(1, threshold=0.7)
        assert len(high) >= 1

    def test_evidence_weight_clamped(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        updated = service.add_evidence(hypo.id, "Over weight", supports=True, weight=5.0)
        assert updated.evidence_for[0]["weight"] == 1.0  # Clamped to 1.0

    def test_confidence_history_growth(self, service):
        hypo = service.generate_hypothesis(user_id=1, hypothesis="H1")
        for i in range(3):
            hypo = service.add_evidence(hypo.id, f"Evidence {i}", supports=True, weight=0.5)
        assert len(hypo.confidence_history) == 4  # creation + 3 evidence

    def test_get_user_hypotheses_with_status(self, service):
        service.generate_hypothesis(user_id=1, hypothesis="A1")
        h2 = service.generate_hypothesis(user_id=1, hypothesis="A2")
        service.resolve_hypothesis(h2.id, "confirmed")

        active = service.get_user_hypotheses(1, status="active")
        confirmed = service.get_user_hypotheses(1, status="confirmed")
        assert len(active) == 1
        assert len(confirmed) == 1
