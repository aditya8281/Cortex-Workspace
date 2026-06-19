"""Tests for Memory API endpoints."""
import pytest

AUTH_HEADER = {"Authorization": "Bearer test-token"}


def test_list_memory_empty(client):
    resp = client.get("/api/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["entries"] == []


def test_create_memory(client):
    resp = client.post(
        "/api/memory",
        json={"title": "Test Entry", "content": "This is test content", "category": "note"},
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"
    assert data["entry"]["title"] == "Test Entry"


def test_create_memory_with_tags(client):
    resp = client.post(
        "/api/memory",
        json={"title": "Tagged", "content": "Content with tags", "tags": ["python", "testing"]},
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    assert resp.json()["entry"]["tags"] == ["python", "testing"]


def test_get_memory(client):
    create_resp = client.post(
        "/api/memory",
        json={"title": "Get Me", "content": "Content"},
        headers=AUTH_HEADER,
    )
    entry_id = create_resp.json()["entry"]["id"]
    resp = client.get(f"/api/memory/{entry_id}")
    assert resp.status_code == 200
    assert resp.json()["entry"]["title"] == "Get Me"


def test_get_memory_not_found(client):
    resp = client.get("/api/memory/99999")
    assert resp.status_code == 404


def test_update_memory(client):
    create_resp = client.post(
        "/api/memory",
        json={"title": "Original", "content": "Original"},
        headers=AUTH_HEADER,
    )
    entry_id = create_resp.json()["entry"]["id"]
    resp = client.put(
        f"/api/memory/{entry_id}",
        json={"title": "Updated", "content": "Updated"},
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    assert resp.json()["entry"]["title"] == "Updated"


def test_delete_memory(client):
    create_resp = client.post(
        "/api/memory",
        json={"title": "Delete Me", "content": "Content"},
        headers=AUTH_HEADER,
    )
    entry_id = create_resp.json()["entry"]["id"]
    resp = client.delete(f"/api/memory/{entry_id}", headers=AUTH_HEADER)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_search_memory(client):
    client.post(
        "/api/memory",
        json={"title": "Python", "content": "Python decorators"},
        headers=AUTH_HEADER,
    )
    client.post(
        "/api/memory",
        json={"title": "Docker", "content": "Docker setup"},
        headers=AUTH_HEADER,
    )
    resp = client.post("/api/memory/search", json={"query": "Python"}, headers=AUTH_HEADER)
    assert resp.status_code == 200
    assert isinstance(resp.json()["results"], list)


def test_list_memory_category_filter(client):
    client.post(
        "/api/memory",
        json={"title": "N1", "content": "C1", "category": "note"},
        headers=AUTH_HEADER,
    )
    client.post(
        "/api/memory",
        json={"title": "C1", "content": "C2", "category": "code"},
        headers=AUTH_HEADER,
    )
    resp = client.get("/api/memory?category=note")
    assert resp.status_code == 200
    assert all(e["category"] == "note" for e in resp.json()["entries"])
