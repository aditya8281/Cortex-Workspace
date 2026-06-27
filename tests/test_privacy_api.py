"""Integration tests for v1.05 P04 privacy API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.core.db import get_current_user
from backend.app.main import app

AUTH_HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def authed_client(client: TestClient) -> TestClient:
    """TestClient with authenticated user override applied per-test."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test_user"
    mock_user.role = "user"
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ── Audit ──────────────────────────────────────────────────────────────


class TestAuditAPI:
    def test_get_audit_logs_empty(self, authed_client: TestClient):
        """GET /audit/logs returns empty list when no logs exist."""
        response = authed_client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_audit_log_count(self, authed_client: TestClient):
        """GET /audit/logs/count returns count."""
        response = authed_client.get("/api/v1/audit/logs/count")
        assert response.status_code == 200
        assert "count" in response.json()

    def test_get_recent_activity(self, authed_client: TestClient):
        """GET /audit/activity returns activity list."""
        response = authed_client.get("/api/v1/audit/activity?limit=20")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── Consent ────────────────────────────────────────────────────────────


class TestConsentAPI:
    def test_grant_and_check_consent(self, authed_client: TestClient):
        """Full consent lifecycle: grant → check → revoke → check."""
        # Grant
        response = authed_client.post(
            "/api/v1/consent/grant",
            json={"consent_type": "memory_read", "scope": "all"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        consent = response.json()
        assert consent["consent_type"] == "memory_read"
        assert consent["granted"] == 1

        # Check
        response = authed_client.get("/api/v1/consent/check?consent_type=memory_read")
        assert response.status_code == 200
        assert response.json()["granted"] is True

        # Revoke
        response = authed_client.post(
            "/api/v1/consent/revoke?consent_type=memory_read",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Check again
        response = authed_client.get("/api/v1/consent/check?consent_type=memory_read")
        assert response.json()["granted"] is False

    def test_get_consents(self, authed_client: TestClient):
        """GET /consent/ returns list of consent records."""
        response = authed_client.get("/api/v1/consent/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_revoke_nonexistent_returns_false(self, authed_client: TestClient):
        """Revoking nonexistent consent returns success=False."""
        response = authed_client.post(
            "/api/v1/consent/revoke?consent_type=nope",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["success"] is False


# ── Export ─────────────────────────────────────────────────────────────


class TestExportAPI:
    def test_create_export(self, authed_client: TestClient):
        """POST /export/create creates a pending export."""
        response = authed_client.post(
            "/api/v1/export/create",
            json={"export_type": "full", "format": "json"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        export = response.json()
        assert export["status"] == "pending"
        assert export["format"] == "json"
        assert export["export_type"] == "full"

    def test_create_partial_export(self, authed_client: TestClient):
        """POST /export/create with data_types creates partial export."""
        response = authed_client.post(
            "/api/v1/export/create",
            json={
                "export_type": "partial",
                "format": "csv",
                "data_types": ["memories", "files"],
            },
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        export = response.json()
        assert export["export_type"] == "partial"
        assert export["format"] == "csv"


# ── Transparency ───────────────────────────────────────────────────────


class TestTransparencyAPI:
    def test_explain_decision(self, authed_client: TestClient):
        """POST /transparency/explain returns structured explanation."""
        response = authed_client.post(
            "/api/v1/transparency/explain",
            json={
                "decision_type": "memory_retrieval",
                "context": {"confidence": 0.85},
            },
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        explanation = response.json()
        assert explanation["decision_type"] == "memory_retrieval"
        assert explanation["confidence"] == 0.85
        assert "factors" in explanation
        assert "recommendation" in explanation

    def test_get_templates(self, authed_client: TestClient):
        """GET /transparency/templates returns template definitions."""
        response = authed_client.get("/api/v1/transparency/templates")
        assert response.status_code == 200
        templates = response.json()
        assert "memory_retrieval" in templates
        assert "tool_selection" in templates


# ── Access Control ─────────────────────────────────────────────────────


class TestAccessControlAPI:
    def test_check_access_returns_result(self, authed_client: TestClient):
        """GET /access/check returns access permission."""
        response = authed_client.get("/api/v1/access/check?resource_type=memory&action=read")
        assert response.status_code == 200
        result = response.json()
        assert "allowed" in result
        assert "resource_type" in result
        assert result["resource_type"] == "memory"

    def test_get_my_roles(self, authed_client: TestClient):
        """GET /access/roles returns user's roles."""
        response = authed_client.get("/api/v1/access/roles")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_my_permissions(self, authed_client: TestClient):
        """GET /access/permissions returns user's permissions."""
        response = authed_client.get("/api/v1/access/permissions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ── End-to-End ─────────────────────────────────────────────────────────


class TestFullPrivacyFlow:
    def test_consent_gates_data_access(self, authed_client: TestClient, db_session):  # type: ignore[no-untyped-def]
        """End-to-end: grant consent → check access → export → explain."""
        # 1. Setup: create role with memory:read permission, assign to user
        from backend.app.models.privacy.role import Permission, Role

        role = Role(name="memory_reader")
        perm = Permission(resource_type="memory", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()

        # 2. Grant consent
        resp = authed_client.post(
            "/api/v1/consent/grant",
            json={"consent_type": "memory_read", "scope": "all"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200

        # 3. Check access (no role assigned yet — should be False)
        resp = authed_client.get("/api/v1/access/check?resource_type=memory&action=read")
        assert resp.status_code == 200
        assert resp.json()["allowed"] is False

        # 4. Assign role
        resp = authed_client.post(
            "/api/v1/access/roles/assign?target_user_id=1",
            json={"name": "memory_reader"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200

        # 5. Check access again (now with role — should be True)
        resp = authed_client.get("/api/v1/access/check?resource_type=memory&action=read")
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

        # 6. Check consent
        resp = authed_client.get("/api/v1/consent/check?consent_type=memory_read")
        assert resp.json()["granted"] is True

        # 7. Create export
        resp = authed_client.post(
            "/api/v1/export/create",
            json={"export_type": "full", "format": "json"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200

        # 8. Explain a decision
        resp = authed_client.post(
            "/api/v1/transparency/explain",
            json={"decision_type": "memory_retrieval", "context": {"confidence": 0.9}},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["confidence"] == 0.9
