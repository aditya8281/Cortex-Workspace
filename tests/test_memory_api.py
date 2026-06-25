"""Tests for the memory API endpoints."""

from fastapi.testclient import TestClient

HEADERS = {"Authorization": "Bearer fake-token"}


def test_list_memory_empty(client: TestClient, mock_auth):
    """GET /api/v1/memory returns empty list when no entries exist."""
    response = client.get("/api/v1/memory", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["count"] == 0
    assert data["entries"] == []
    assert isinstance(data["categories"], dict)


def test_list_memory_with_entries(client: TestClient, mock_auth, db_session):
    """GET /api/v1/memory returns entries with correct structure."""
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    manager.create(
        user_id=mock_auth.id,
        title="Test Memory",
        content="This is test content",
        category="fact",
    )

    response = client.get("/api/v1/memory", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["count"] == 1
    assert len(data["entries"]) == 1
    assert data["entries"][0]["title"] == "Test Memory"
    assert data["entries"][0]["category"] == "fact"


def test_list_memory_with_category_filter(client: TestClient, mock_auth, db_session):
    """GET /api/v1/memory with category filter returns only matching entries."""
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    manager.create(user_id=mock_auth.id, title="Fact 1", content="Content 1", category="fact")
    manager.create(user_id=mock_auth.id, title="Pattern 1", content="Content 2", category="pattern")

    response = client.get("/api/v1/memory?category=fact", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["entries"][0]["category"] == "fact"


def test_create_memory(client: TestClient, mock_auth):
    """POST /api/v1/memory creates a new memory entry."""
    response = client.post(
        "/api/v1/memory",
        json={
            "title": "New Memory",
            "content": "Important information",
            "category": "preference",
            "tags": ["ai", "cortex"],
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["entry"]["title"] == "New Memory"
    assert data["entry"]["category"] == "preference"
    assert data["entry"]["tags"] == ["ai", "cortex"]


def test_create_memory_minimal(client: TestClient, mock_auth):
    """POST /api/v1/memory with minimal fields uses defaults."""
    response = client.post(
        "/api/v1/memory",
        json={
            "title": "Minimal Memory",
            "content": "Just content",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["entry"]["category"] == "note"  # Default from MemoryCreatePayload


def test_create_memory_invalid_category(client: TestClient, mock_auth):
    """POST /api/v1/memory with invalid category returns error."""
    response = client.post(
        "/api/v1/memory",
        json={
            "title": "Bad Memory",
            "content": "Content",
            "category": "invalid_category",
        },
        headers=HEADERS,
    )
    assert response.status_code == 422  # Validation error


def test_get_memory(client: TestClient, mock_auth, db_session):
    """GET /api/v1/memory/{id} returns a specific memory."""
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    entry = manager.create(
        user_id=mock_auth.id,
        title="Get Me",
        content="Fetch this",
        category="fact",
    )

    response = client.get(f"/api/v1/memory/{entry.id}", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Get Me"
    assert data["id"] == entry.id


def test_get_memory_not_found(client: TestClient, mock_auth):
    """GET /api/v1/memory/{id} with nonexistent ID returns 404."""
    response = client.get("/api/v1/memory/99999", headers=HEADERS)
    assert response.status_code == 404


def test_update_memory(client: TestClient, mock_auth, db_session):
    """PUT /api/v1/memory/{id} updates an existing memory."""
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    entry = manager.create(
        user_id=mock_auth.id,
        title="Original",
        content="Original content",
        category="fact",
    )

    response = client.put(
        f"/api/v1/memory/{entry.id}",
        json={
            "title": "Updated",
            "content": "Updated content",
            "category": "pattern",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["entry"]["title"] == "Updated"
    assert data["entry"]["category"] == "pattern"


def test_update_memory_not_found(client: TestClient, mock_auth):
    """PUT /api/v1/memory/{id} with nonexistent ID returns 404."""
    response = client.put(
        "/api/v1/memory/99999",
        json={"title": "Updated"},
        headers=HEADERS,
    )
    assert response.status_code == 404


def test_delete_memory(client: TestClient, mock_auth, db_session):
    """DELETE /api/v1/memory/{id} deletes a memory."""
    from backend.app.intelligence.models import KnowledgeEntry
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    entry = manager.create(
        user_id=mock_auth.id,
        title="Delete Me",
        content="Gone soon",
        category="fact",
    )
    entry_id = entry.id

    response = client.delete(f"/api/v1/memory/{entry_id}", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"

    # Verify hard delete - entry should be completely removed
    db_session.expire_all()  # Clear session cache
    deleted_entry = db_session.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
    assert deleted_entry is None


def test_delete_memory_not_found(client: TestClient, mock_auth):
    """DELETE /api/v1/memory/{id} with nonexistent ID returns 404."""
    response = client.delete("/api/v1/memory/99999", headers=HEADERS)
    assert response.status_code == 404


def test_search_memory(client: TestClient, mock_auth, db_session):
    """POST /api/v1/memory/search performs semantic search."""
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    manager.create(
        user_id=mock_auth.id,
        title="Python Tips",
        content="Use list comprehensions for better performance",
        category="pattern",
    )

    response = client.post(
        "/api/v1/memory/search",
        json={"query": "python performance", "limit": 5},
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "python performance"
    assert isinstance(data["results"], list)


def test_search_memory_empty_query(client: TestClient, mock_auth):
    """POST /api/v1/memory/search with empty query returns error."""
    response = client.post(
        "/api/v1/memory/search",
        json={"query": "", "limit": 5},
        headers=HEADERS,
    )
    assert response.status_code == 422  # Validation error


def test_list_memory_pagination(client: TestClient, mock_auth, db_session):
    """GET /api/v1/memory respects limit and offset parameters."""
    from backend.app.services.memory_manager import MemoryManager

    manager = MemoryManager(db_session)
    for i in range(5):
        manager.create(
            user_id=mock_auth.id,
            title=f"Memory {i}",
            content=f"Content {i}",
            category="fact",
        )

    # Get first 2
    response = client.get("/api/v1/memory?limit=2&offset=0", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["count"] == 2
    assert len(data["entries"]) == 2

    # Get next 2
    response = client.get("/api/v1/memory?limit=2&offset=2", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["entries"][0]["title"] == "Memory 2"


def test_unauthorized_access(client: TestClient):
    """Endpoints return 401 without auth token (or 403 CSRF for POST/PUT/DELETE)."""
    endpoints = [
        ("GET", "/api/v1/memory"),
        ("POST", "/api/v1/memory"),
        ("GET", "/api/v1/memory/1"),
        ("PUT", "/api/v1/memory/1"),
        ("DELETE", "/api/v1/memory/1"),
        ("POST", "/api/v1/memory/search"),
    ]

    for method, url in endpoints:
        response = client.request(method, url, json={"title": "test"} if method == "POST" else None)
        # GET returns 401 (unauthorized), POST/PUT/DELETE return 403 (CSRF) when no Bearer token
        assert response.status_code in (401, 403, 429), (
            f"{method} {url} should require auth, got {response.status_code}"
        )
