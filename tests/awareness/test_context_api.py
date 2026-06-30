"""Integration tests for awareness context API routes (system, attention, context)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

AUTH_HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def auth_client(client: TestClient, mock_auth: MagicMock) -> TestClient:
    """Authenticated TestClient for awareness context API tests."""
    return client


# ── System routes ────────────────────────────────────────────────────────────


class TestSystemRoutes:
    """Tests for /api/v1/awareness/system/ endpoints."""

    def test_take_snapshot(self, auth_client: TestClient) -> None:
        """POST /system/snapshot returns snapshot data."""
        resp = auth_client.post("/api/v1/awareness/system/snapshot", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "created_at" in data

    def test_get_recent(self, auth_client: TestClient) -> None:
        """GET /system/recent returns snapshot list."""
        resp = auth_client.get("/api/v1/awareness/system/recent", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshots" in data
        assert "total" in data

    def test_get_recent_empty(self, auth_client: TestClient) -> None:
        """GET /system/recent with no snapshots returns empty list."""
        resp = auth_client.get("/api/v1/awareness/system/recent", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_get_anomalies(self, auth_client: TestClient) -> None:
        """GET /system/anomalies returns anomaly list."""
        resp = auth_client.get("/api/v1/awareness/system/anomalies", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert "anomalies" in resp.json()

    def test_snapshot_no_auth(self, client: TestClient) -> None:
        """POST /system/snapshot without auth returns 401."""
        resp = client.post("/api/v1/awareness/system/snapshot")
        assert resp.status_code in (401, 403)


# ── Attention routes ─────────────────────────────────────────────────────────


class TestAttentionRoutes:
    """Tests for /api/v1/awareness/attention/ endpoints."""

    def test_start_session(self, auth_client: TestClient) -> None:
        """POST /attention/session creates a session."""
        resp = auth_client.post(
            "/api/v1/awareness/attention/session",
            json={"session_type": "coding", "task_description": "test"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_type"] == "coding"
        assert data["task_description"] == "test"
        assert "id" in data
        assert "started_at" in data

    def test_start_session_defaults(self, auth_client: TestClient) -> None:
        """POST /attention/session with empty body uses defaults."""
        resp = auth_client.post(
            "/api/v1/awareness/attention/session",
            json={},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["session_type"] == "general"

    def test_end_session_not_found(self, auth_client: TestClient) -> None:
        """POST /attention/session/999/end returns 404."""
        resp = auth_client.post(
            "/api/v1/awareness/attention/session/999/end",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_get_sessions(self, auth_client: TestClient) -> None:
        """GET /attention/sessions returns session list."""
        resp = auth_client.get("/api/v1/awareness/attention/sessions", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert "total" in data

    def test_get_stats(self, auth_client: TestClient) -> None:
        """GET /attention/stats returns aggregated stats."""
        resp = auth_client.get("/api/v1/awareness/attention/stats", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sessions" in data
        assert "sessions_by_type" in data

    def test_start_session_no_auth(self, client: TestClient) -> None:
        """POST /attention/session without auth returns 401."""
        resp = client.post(
            "/api/v1/awareness/attention/session",
            json={"session_type": "coding"},
        )
        assert resp.status_code in (401, 403)


# ── Context routes ───────────────────────────────────────────────────────────


class TestContextRoutes:
    """Tests for /api/v1/awareness/context/ endpoints."""

    # -- Rules --

    def test_create_rule(self, auth_client: TestClient) -> None:
        """POST /context/rules creates a rule."""
        resp = auth_client.post(
            "/api/v1/awareness/context/rules",
            json={"name": "test", "rule_type": "time", "conditions": {}, "actions": {}},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test"
        assert data["rule_type"] == "time"
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_rules(self, auth_client: TestClient) -> None:
        """GET /context/rules returns rule list."""
        resp = auth_client.get("/api/v1/awareness/context/rules", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_rules_by_type(self, auth_client: TestClient) -> None:
        """GET /context/rules?rule_type=time filters by type."""
        resp = auth_client.get("/api/v1/awareness/context/rules?rule_type=time", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_update_rule_not_found(self, auth_client: TestClient) -> None:
        """PUT /context/rules/999 returns 404."""
        resp = auth_client.put(
            "/api/v1/awareness/context/rules/999?name=x&priority=1",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code in (404, 500)

    def test_delete_rule_not_found(self, auth_client: TestClient) -> None:
        """DELETE /context/rules/999 returns 404."""
        resp = auth_client.delete("/api/v1/awareness/context/rules/999", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    # -- State --

    def test_set_state(self, auth_client: TestClient) -> None:
        """PUT /context/state/{key} upserts state."""
        resp = auth_client.put(
            "/api/v1/awareness/context/state/current_app",
            json={"name": "code"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["state_key"] == "current_app"
        assert data["state_value"] == {"name": "code"}
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_all_state(self, auth_client: TestClient) -> None:
        """GET /context/state returns state list."""
        resp = auth_client.get("/api/v1/awareness/context/state", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_state_not_found(self, auth_client: TestClient) -> None:
        """GET /context/state/nonexistent returns 404."""
        resp = auth_client.get(
            "/api/v1/awareness/context/state/nonexistent",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    # -- Events --

    def test_log_event(self, auth_client: TestClient) -> None:
        """POST /context/events logs an event."""
        resp = auth_client.post(
            "/api/v1/awareness/context/events",
            json={"event_type": "app_switch", "event_data": {"app": "code"}},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == "app_switch"
        assert "created_at" in data

    def test_log_event_defaults(self, auth_client: TestClient) -> None:
        """POST /context/events with minimal payload uses defaults."""
        resp = auth_client.post(
            "/api/v1/awareness/context/events",
            json={"event_type": "custom"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "system"
        assert data["relevance_score"] == 0.0

    def test_get_events(self, auth_client: TestClient) -> None:
        """GET /context/events returns event list."""
        resp = auth_client.get("/api/v1/awareness/context/events", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_events_by_type(self, auth_client: TestClient) -> None:
        """GET /context/events?event_type=X filters by type."""
        resp = auth_client.get(
            "/api/v1/awareness/context/events?event_type=app_switch",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    # -- Auth --

    def test_rules_no_auth(self, client: TestClient) -> None:
        """POST /context/rules without auth returns 401."""
        resp = client.post(
            "/api/v1/awareness/context/rules",
            json={"name": "x", "rule_type": "time", "conditions": {}, "actions": {}},
        )
        assert resp.status_code in (401, 403)

    def test_events_no_auth(self, client: TestClient) -> None:
        """POST /context/events without auth returns 401."""
        resp = client.post(
            "/api/v1/awareness/context/events",
            json={"event_type": "click"},
        )
        assert resp.status_code in (401, 403)
