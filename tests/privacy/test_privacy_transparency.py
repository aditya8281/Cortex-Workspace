"""Tests for v1.05 P03 transparency service."""

from __future__ import annotations

from backend.app.services.privacy.transparency import TransparencyService


class TestTransparencyService:
    def test_explain_decision(self) -> None:
        service = TransparencyService()
        result = service.explain_decision(
            "memory_retrieval",
            {"confidence": 0.85, "query_similarity": 0.9, "recency": "2026-06-01"},
        )
        assert result["decision_type"] == "memory_retrieval"
        assert result["confidence"] == 0.85
        assert result["risk_level"] == "low"
        assert len(result["factors"]) > 0
        assert len(result["alternatives_considered"]) > 0
        assert "recommendation" in result

    def test_explain_unknown_decision(self) -> None:
        service = TransparencyService()
        result = service.explain_decision("unknown_type", {})
        assert result["decision_type"] == "unknown_type"
        assert result["confidence"] == 0.5
        assert result["risk_level"] == "medium"

    def test_risk_levels(self) -> None:
        service = TransparencyService()
        high_conf = service.explain_decision("test", {"confidence": 0.9})
        assert high_conf["risk_level"] == "low"
        low_conf = service.explain_decision("test", {"confidence": 0.2})
        assert low_conf["risk_level"] == "high"

    def test_all_template_types(self) -> None:
        service = TransparencyService()
        for dtype in service.DECISION_TEMPLATES:
            result = service.explain_decision(dtype, {"confidence": 0.7})
            assert result["decision_type"] == dtype
            assert isinstance(result["factors"], list)
