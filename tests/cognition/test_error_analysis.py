"""Tests for ErrorAnalysisService."""

from backend.app.models.cognition.error_analysis import ErrorAnalysis
from backend.app.services.cognition.error_analysis import ErrorAnalysisService


class TestErrorAnalysisService:
    """Error analysis service tests."""

    def test_analyze_error(self, db_session):
        service = ErrorAnalysisService(db_session)
        analysis = service.analyze_error(
            user_id=1,
            error_type="ValueError",
            error_message="invalid value for field x",
            context={"field": "x", "value": "abc"},
        )
        assert analysis.id is not None
        assert analysis.error_type == "ValueError"
        assert analysis.fingerprint is not None
        assert analysis.severity == "error"
        assert analysis.root_cause is not None
        assert analysis.resolution is not None

    def test_fingerprint_normalization(self, db_session):
        service = ErrorAnalysisService(db_session)
        # Two errors with different paths/numbers should get the same fingerprint
        a1 = service.analyze_error(
            user_id=1,
            error_type="IOError",
            error_message="File /tmp/data/file42.txt not found on server 3",
        )
        a2 = service.analyze_error(
            user_id=1,
            error_type="IOError",
            error_message="File /home/user/file99.txt not found on server 7",
        )
        assert a1.fingerprint == a2.fingerprint
        assert "{path}" in a1.fingerprint or "{num}" in a1.fingerprint

        # UUIDs should be normalized too
        a3 = service.analyze_error(
            user_id=1,
            error_type="SecurityError",
            error_message="Session 550e8400-e29b-41d4-a716-446655440000 expired",
        )
        assert "{uuid}" in a3.fingerprint

    def test_error_patterns(self, db_session):
        service = ErrorAnalysisService(db_session)
        # Create several errors with the same fingerprint
        for _ in range(3):
            service.analyze_error(
                user_id=1,
                error_type="ValueError",
                error_message="invalid input",
            )
        # One different error
        service.analyze_error(
            user_id=1,
            error_type="TypeError",
            error_message="type mismatch",
        )

        patterns = service.get_error_patterns(user_id=1, days=30)
        assert len(patterns) >= 2

        # The ValueError pattern should have higher count
        val_pattern = next(p for p in patterns if p["error_type"] == "ValueError")
        assert val_pattern["count"] == 3

        type_pattern = next(p for p in patterns if p["error_type"] == "TypeError")
        assert type_pattern["count"] == 1

    def test_resolve_error(self, db_session):
        service = ErrorAnalysisService(db_session)
        analysis = service.analyze_error(
            user_id=1,
            error_type="TimeoutError",
            error_message="connection timed out",
        )
        assert analysis.resolved == 0

        resolved = service.resolve_error(analysis.id, resolution_method="retry")
        assert resolved.resolved == 1
        assert resolved.resolution_method == "retry"
        assert resolved.resolved_at is not None

    def test_severity_classification(self, db_session):
        service = ErrorAnalysisService(db_session)
        sev = service.analyze_error(
            user_id=1,
            error_type="SecurityError",
            error_message="access denied",
        )
        assert sev.severity == "critical"

        warn = service.analyze_error(
            user_id=1,
            error_type="DeprecationWarning",
            error_message="old API",
        )
        assert warn.severity == "warning"

        info = service.analyze_error(
            user_id=1,
            error_type="UnknownError",
            error_message="something odd",
        )
        assert info.severity == "info"

    def test_resolution_pattern_matching(self, db_session):
        service = ErrorAnalysisService(db_session)
        # "invalid" in the message should match ValueError:invalid pattern
        analysis = service.analyze_error(
            user_id=1,
            error_type="ValueError",
            error_message="invalid parameter provided",
        )
        assert "input parameters" in analysis.resolution

        # Different message keyword should pick a different pattern
        analysis2 = service.analyze_error(
            user_id=1,
            error_type="IOError",
            error_message="file not found",
        )
        assert "file exists" in analysis2.resolution

    def test_root_cause_from_history(self, db_session):
        service = ErrorAnalysisService(db_session)
        # Seed a historical analysis with a specific root cause
        historical = ErrorAnalysis(
            user_id=1,
            error_type="ValueError",
            error_message="bad input",
            fingerprint="ValueError:bad_input",
            root_cause="User provided null value where string expected",
            severity="error",
        )
        db_session.add(historical)
        db_session.commit()

        # New similar error should inherit the historical root cause
        analysis = service.analyze_error(
            user_id=1,
            error_type="ValueError",
            error_message="bad input",
        )
        assert "null value" in analysis.root_cause

    def test_get_user_analyses(self, db_session):
        service = ErrorAnalysisService(db_session)
        service.analyze_error(user_id=1, error_type="ValueError", error_message="e1")
        service.analyze_error(user_id=1, error_type="TypeError", error_message="e2")
        service.analyze_error(user_id=2, error_type="RuntimeError", error_message="e3")

        # User 1 should see 2 analyses
        user1 = service.get_user_analyses(user_id=1)
        assert len(user1) == 2

        # Filter by severity
        user1_error = service.get_user_analyses(user_id=1, severity="error")
        assert len(user1_error) >= 1

        # User 2 should see 1 analysis
        user2 = service.get_user_analyses(user_id=2)
        assert len(user2) == 1
