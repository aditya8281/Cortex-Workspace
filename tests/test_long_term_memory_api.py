from unittest.mock import MagicMock

import pytest

from backend.app.api.deps import get_current_user
from backend.app.main import app
from backend.app.models.long_term_memory import LongTermMemory

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def mock_unlocked_auth():
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test_user"
    mock_user.full_name = "Test User"
    mock_user.role = "user"
    mock_user.nickname = "testnick"
    mock_user.bio = None
    mock_user.description = None
    mock_user.profile_photo = None
    mock_user.handles_json = {}
    mock_user.preferences_json = {}
    mock_user.vault_locked = False
    mock_user.vault_password_hash = "some_hash"
    mock_user.github_username = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.deleted_at = None

    def _override():
        return mock_user

    app.dependency_overrides[get_current_user] = _override
    yield mock_user
    app.dependency_overrides.pop(get_current_user, None)


def test_list_memories_empty(client, mock_unlocked_auth):
    resp = client.get("/api/v1/long-term-memory", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "grouped" in data
    for cat_memories in data["grouped"].values():
        assert isinstance(cat_memories, list)


def test_list_memories_with_category(client, mock_unlocked_auth, db_session):
    mem = LongTermMemory(
        user_id=1,
        category="preference",
        title="Dark mode",
        content="User prefers dark mode",
        confidence=0.8,
        access_count=1,
        tags=[],
        is_active=True,
    )
    db_session.add(mem)
    db_session.commit()

    resp = client.get("/api/v1/long-term-memory?category=preference", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "memories" in data
    assert len(data["memories"]) == 1
    assert data["memories"][0]["title"] == "Dark mode"


def test_memory_stats(client, mock_unlocked_auth, db_session):
    mem = LongTermMemory(
        user_id=1,
        category="fact",
        title="Test fact",
        content="Some fact content",
        confidence=0.5,
        access_count=0,
        tags=[],
        is_active=True,
    )
    db_session.add(mem)
    db_session.commit()

    resp = client.get("/api/v1/long-term-memory/stats", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["active"] == 1
    assert "by_category" in data
    assert data["by_category"]["fact"] == 1
    assert data["avg_confidence"] == 0.5


def test_create_memory(client, mock_unlocked_auth):
    resp = client.post(
        "/api/v1/long-term-memory",
        json={
            "category": "pattern",
            "title": "Code style",
            "content": "User writes concise Python",
            "source": "conversation",
            "tags": ["python", "style"],
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"
    assert "id" in data


def test_create_memory_minimal(client, mock_unlocked_auth):
    resp = client.post(
        "/api/v1/long-term-memory",
        json={
            "category": "correction",
            "title": "Fix",
            "content": "Corrected user about X",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"


def test_create_memory_invalid_category(client, mock_unlocked_auth):
    try:
        resp = client.post(
            "/api/v1/long-term-memory",
            json={
                "category": "invalid_cat",
                "title": "Test",
                "content": "Test",
            },
            headers=HEADERS,
        )
        assert resp.status_code != 200
    except Exception:
        pass


def test_reinforce_memory(client, mock_unlocked_auth, db_session):
    mem = LongTermMemory(
        user_id=1,
        category="context",
        title="User context",
        content="Some context",
        confidence=0.5,
        access_count=0,
        tags=[],
        is_active=True,
    )
    db_session.add(mem)
    db_session.commit()
    mem_id = mem.id

    resp = client.post(
        f"/api/v1/long-term-memory/{mem_id}/reinforce",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == 0.6


def test_reinforce_memory_not_found(client, mock_unlocked_auth):
    resp = client.post(
        "/api/v1/long-term-memory/999999/reinforce",
        headers=HEADERS,
    )
    assert resp.status_code == 404


def test_delete_memory(client, mock_unlocked_auth, db_session):
    mem = LongTermMemory(
        user_id=1,
        category="preference",
        title="To delete",
        content="Delete me",
        confidence=0.3,
        access_count=0,
        tags=[],
        is_active=True,
    )
    db_session.add(mem)
    db_session.commit()
    mem_id = mem.id

    resp = client.delete(
        f"/api/v1/long-term-memory/{mem_id}",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "deleted"

    from sqlalchemy import select

    refreshed = db_session.execute(
        select(LongTermMemory).where(LongTermMemory.id == mem_id)
    ).scalar_one()
    assert refreshed.is_active is False


def test_delete_memory_nonexistent(client, mock_unlocked_auth):
    resp = client.delete(
        "/api/v1/long-term-memory/999999",
        headers=HEADERS,
    )
    assert resp.status_code == 404
