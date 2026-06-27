"""Integration tests for v1.03 Cortex memory API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

AUTH_HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def auth_client(client: TestClient, mock_auth: MagicMock) -> TestClient:
    """Re-use conftest's client + mock_auth to get an authenticated TestClient."""
    return client


@pytest.fixture()
def unauth_client(client: TestClient) -> TestClient:
    """TestClient without auth override — for testing 401 responses."""
    from backend.app.api.deps import get_current_user

    app.dependency_overrides.pop(get_current_user, None)
    return client


# ---------------------------------------------------------------------------
# Episodic Memory CRUD
# ---------------------------------------------------------------------------


class TestEpisodicAPI:
    def test_create_episodic(self, auth_client: TestClient) -> None:
        resp = auth_client.post(
            "/api/v1/episodic",
            json={
                "content": "Learned about exponential decay",
                "importance": 0.8,
                "emotion": "curious",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["content"] == "Learned about exponential decay"
        assert body["importance"] == 0.8
        assert body["emotion"] == "curious"
        assert body["id"] > 0

    def test_list_episodic(self, auth_client: TestClient) -> None:
        for i in range(3):
            auth_client.post("/api/v1/episodic", json={"content": f"Memory {i}"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/episodic?limit=10", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 3
        assert len(body["memories"]) >= 3

    def test_get_episodic_by_id(self, auth_client: TestClient) -> None:
        create = auth_client.post("/api/v1/episodic", json={"content": "Specific"}, headers=AUTH_HEADERS)
        mid = create.json()["id"]
        resp = auth_client.get(f"/api/v1/episodic/{mid}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["content"] == "Specific"

    def test_get_episodic_404(self, auth_client: TestClient) -> None:
        resp = auth_client.get("/api/v1/episodic/99999", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_update_episodic(self, auth_client: TestClient) -> None:
        create = auth_client.post("/api/v1/episodic", json={"content": "Original"}, headers=AUTH_HEADERS)
        mid = create.json()["id"]
        resp = auth_client.patch(f"/api/v1/episodic/{mid}", json={"content": "Updated"}, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["content"] == "Updated"

    def test_delete_episodic(self, auth_client: TestClient) -> None:
        create = auth_client.post("/api/v1/episodic", json={"content": "Delete me"}, headers=AUTH_HEADERS)
        mid = create.json()["id"]
        resp = auth_client.delete(f"/api/v1/episodic/{mid}", headers=AUTH_HEADERS)
        assert resp.status_code == 204
        assert auth_client.get(f"/api/v1/episodic/{mid}", headers=AUTH_HEADERS).status_code == 404

    def test_search_episodic(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/episodic", json={"content": "Python debugging tips"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/episodic/search?query=Python", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


# ---------------------------------------------------------------------------
# Semantic Memory CRUD
# ---------------------------------------------------------------------------


class TestSemanticAPI:
    def test_create_semantic(self, auth_client: TestClient) -> None:
        resp = auth_client.post(
            "/api/v1/semantic",
            json={
                "content": "FastAPI uses ASGI",
                "category": "fact",
                "source": "docs",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "FastAPI uses ASGI"

    def test_semantic_dedup(self, auth_client: TestClient) -> None:
        auth_client.post(
            "/api/v1/semantic", json={"content": "Duplicate fact", "category": "fact"}, headers=AUTH_HEADERS
        )
        resp = auth_client.post(
            "/api/v1/semantic", json={"content": "Duplicate fact", "category": "fact"}, headers=AUTH_HEADERS
        )
        assert resp.status_code == 201
        assert resp.json()["confidence"] > 0.5

    def test_list_semantic_with_category(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/semantic", json={"content": "A", "category": "x"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/semantic?category=x", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_semantic_categories(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/semantic", json={"content": "C", "category": "y"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/semantic/categories", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_search_semantic(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/semantic", json={"content": "Python typing module"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/semantic/search?query=Python", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_update_semantic(self, auth_client: TestClient) -> None:
        create = auth_client.post("/api/v1/semantic", json={"content": "Old"}, headers=AUTH_HEADERS)
        mid = create.json()["id"]
        resp = auth_client.patch(f"/api/v1/semantic/{mid}", json={"content": "New"}, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["content"] == "New"

    def test_delete_semantic(self, auth_client: TestClient) -> None:
        create = auth_client.post("/api/v1/semantic", json={"content": "Gone"}, headers=AUTH_HEADERS)
        mid = create.json()["id"]
        resp = auth_client.delete(f"/api/v1/semantic/{mid}", headers=AUTH_HEADERS)
        assert resp.status_code == 204
        assert auth_client.get(f"/api/v1/semantic/{mid}", headers=AUTH_HEADERS).status_code == 404


# ---------------------------------------------------------------------------
# Working Memory CRUD
# ---------------------------------------------------------------------------


class TestWorkingMemoryAPI:
    def test_add_working_memory(self, auth_client: TestClient) -> None:
        resp = auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-1",
                "content": "Current task: P05",
                "slot": "active",
                "priority": 5,
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Current task: P05"

    def test_get_working_memory(self, auth_client: TestClient) -> None:
        auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-2",
                "content": "A",
            },
            headers=AUTH_HEADERS,
        )
        resp = auth_client.get("/api/v1/working?session_id=sess-2", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_promote_working_memory(self, auth_client: TestClient) -> None:
        create = auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-3",
                "content": "B",
                "slot": "buffer",
            },
            headers=AUTH_HEADERS,
        )
        mid = create.json()["id"]
        resp = auth_client.post(f"/api/v1/working/{mid}/promote", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["promoted"] is True

    def test_archive_working_memory(self, auth_client: TestClient) -> None:
        create = auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-4",
                "content": "C",
            },
            headers=AUTH_HEADERS,
        )
        mid = create.json()["id"]
        resp = auth_client.post(f"/api/v1/working/{mid}/archive", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["archived"] is True

    def test_demote_working_memory(self, auth_client: TestClient) -> None:
        create = auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-5",
                "content": "D",
            },
            headers=AUTH_HEADERS,
        )
        mid = create.json()["id"]
        resp = auth_client.post(f"/api/v1/working/{mid}/demote", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["demoted"] is True

    def test_remove_working_memory(self, auth_client: TestClient) -> None:
        create = auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-6",
                "content": "E",
            },
            headers=AUTH_HEADERS,
        )
        mid = create.json()["id"]
        resp = auth_client.delete(f"/api/v1/working/{mid}", headers=AUTH_HEADERS)
        assert resp.status_code == 204

    def test_clear_session(self, auth_client: TestClient) -> None:
        for c in ("F", "G"):
            auth_client.post(
                "/api/v1/working",
                json={
                    "session_id": "sess-7",
                    "content": c,
                },
                headers=AUTH_HEADERS,
            )
        resp = auth_client.delete("/api/v1/working/session/sess-7", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["cleared"] >= 2

    def test_session_summary(self, auth_client: TestClient) -> None:
        auth_client.post(
            "/api/v1/working",
            json={
                "session_id": "sess-8",
                "content": "H",
            },
            headers=AUTH_HEADERS,
        )
        resp = auth_client.get("/api/v1/working/session/sess-8/summary", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["active"] >= 1


# ---------------------------------------------------------------------------
# Graph Endpoints
# ---------------------------------------------------------------------------


class TestGraphAPI:
    def test_create_node_and_get_stats(self, auth_client: TestClient) -> None:
        epi = auth_client.post("/api/v1/episodic", json={"content": "Graph node test"}, headers=AUTH_HEADERS)
        epi_id = epi.json()["id"]
        resp = auth_client.post(
            "/api/v1/graph/node",
            json={
                "memory_type": "episodic",
                "memory_id": epi_id,
                "label": "test node",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201

        stats = auth_client.get("/api/v1/graph/stats", headers=AUTH_HEADERS)
        assert stats.status_code == 200
        assert stats.json()["total_nodes"] >= 1

    def test_create_edge(self, auth_client: TestClient) -> None:
        epi1 = auth_client.post("/api/v1/episodic", json={"content": "N1"}, headers=AUTH_HEADERS).json()
        epi2 = auth_client.post("/api/v1/episodic", json={"content": "N2"}, headers=AUTH_HEADERS).json()
        n1 = auth_client.post(
            "/api/v1/graph/node",
            json={
                "memory_type": "episodic",
                "memory_id": epi1["id"],
                "label": "a",
            },
            headers=AUTH_HEADERS,
        ).json()
        n2 = auth_client.post(
            "/api/v1/graph/node",
            json={
                "memory_type": "episodic",
                "memory_id": epi2["id"],
                "label": "b",
            },
            headers=AUTH_HEADERS,
        ).json()
        resp = auth_client.post(
            "/api/v1/graph/edge",
            json={
                "source_id": n1["id"],
                "target_id": n2["id"],
                "edge_type": "related_to",
                "weight": 0.6,
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json()["edge_type"] == "related_to"

    def test_self_loop_rejected(self, auth_client: TestClient) -> None:
        epi = auth_client.post("/api/v1/episodic", json={"content": "SL"}, headers=AUTH_HEADERS).json()
        n = auth_client.post(
            "/api/v1/graph/node",
            json={
                "memory_type": "episodic",
                "memory_id": epi["id"],
                "label": "x",
            },
            headers=AUTH_HEADERS,
        ).json()
        resp = auth_client.post(
            "/api/v1/graph/edge",
            json={
                "source_id": n["id"],
                "target_id": n["id"],
                "edge_type": "self",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400

    def test_strongest_connections(self, auth_client: TestClient) -> None:
        resp = auth_client.get("/api/v1/graph/strongest?limit=5", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_get_connections(self, auth_client: TestClient) -> None:
        epi = auth_client.post("/api/v1/episodic", json={"content": "Conn"}, headers=AUTH_HEADERS).json()
        n = auth_client.post(
            "/api/v1/graph/node",
            json={
                "memory_type": "episodic",
                "memory_id": epi["id"],
                "label": "cn",
            },
            headers=AUTH_HEADERS,
        ).json()
        resp = auth_client.get(f"/api/v1/graph/node/{n['id']}/connections", headers=AUTH_HEADERS)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Search & Forgetting Endpoints
# ---------------------------------------------------------------------------


class TestSearchForgetAPI:
    def test_search_all(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/episodic", json={"content": "Alpha search test"}, headers=AUTH_HEADERS)
        auth_client.post(
            "/api/v1/semantic", json={"content": "Alpha search fact", "category": "x"}, headers=AUTH_HEADERS
        )
        resp = auth_client.get("/api/v1/cortex-search?query=Alpha", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["count"] >= 2

    def test_search_by_importance(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/episodic", json={"content": "High", "importance": 0.95}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/cortex-search/importance?min_importance=0.8", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_search_by_recency(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/episodic", json={"content": "Recent"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/cortex-search/recency?limit=5", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    def test_apply_forgetting(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/forget", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert "episodic_decayed" in resp.json()

    def test_forgetting_stats(self, auth_client: TestClient) -> None:
        auth_client.post("/api/v1/episodic", json={"content": "Stats test"}, headers=AUTH_HEADERS)
        resp = auth_client.get("/api/v1/forget/stats", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total_episodic"] >= 1


# ---------------------------------------------------------------------------
# Auth & Isolation
# ---------------------------------------------------------------------------


class TestAuthAndIsolation:
    def test_unauthenticated_returns_401(self, unauth_client: TestClient) -> None:
        resp = unauth_client.get("/api/v1/episodic", headers=AUTH_HEADERS)
        assert resp.status_code == 401
