"""Tests for conversations API — CRUD, decoupled send/stream pattern."""

import json

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture(autouse=True)
def _clean_stream_manager():
    """Reset the global stream manager between tests to avoid task leaks."""
    from backend.app.services.interaction.stream_manager import stream_manager

    yield
    # Cancel any lingering tasks and clear buffers
    for cid in list(stream_manager._tasks):
        task = stream_manager._tasks[cid]
        if not task.done():
            task.cancel()
    stream_manager._buffers.clear()
    stream_manager._tasks.clear()


def test_list_conversations_empty(client, mock_auth):
    resp = client.get("/api/v1/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversations"] == []
    assert data["total"] == 0


def test_create_conversation(client, mock_auth):
    resp = client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation", "repo_id": None},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Conversation"
    assert data["repo_id"] is None
    assert data["message_count"] == 0
    assert data["total_tokens"] == 0
    assert "id" in data


def test_get_conversation(client, mock_auth, db_session):
    from backend.app.models.interaction.conversation import Conversation

    conv = Conversation(user_id=1, title="Get Me")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    resp = client.get(f"/api/v1/conversations/{conv.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == conv.id
    assert data["title"] == "Get Me"
    assert data["messages"] == []


def test_get_conversation_not_found(client, mock_auth):
    resp = client.get("/api/v1/conversations/99999")
    assert resp.status_code == 404


def test_delete_conversation(client, mock_auth, db_session):
    from backend.app.models.interaction.conversation import Conversation

    conv = Conversation(user_id=1, title="Delete Me")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    resp = client.delete(f"/api/v1/conversations/{conv.id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"

    resp2 = client.get(f"/api/v1/conversations/{conv.id}")
    assert resp2.status_code == 404


def test_delete_conversation_not_found(client, mock_auth):
    resp = client.delete("/api/v1/conversations/99999", headers=HEADERS)
    assert resp.status_code == 404


def test_send_message_starts_generation(client, mock_auth, db_session):
    """Test POST triggers background generation and returns immediately."""
    from backend.app.models.interaction.conversation import Conversation

    conv = Conversation(user_id=1, title="Chat Conv")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    resp = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={"content": "Hi there"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generating"
    assert data["conversation_id"] == conv.id


def test_send_message_already_generating(client, mock_auth, db_session):
    """Test POST when generation is already in progress returns 'generating' without starting another."""
    from backend.app.models.interaction.conversation import Conversation
    from backend.app.services.interaction.stream_manager import stream_manager

    conv = Conversation(user_id=1, title="Chat Conv")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    # Create a buffer to simulate in-progress generation
    stream_manager.get_or_create_buffer(conv.id)

    resp = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={"content": "Hi there"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generating"


def test_stream_no_generation(client, mock_auth, db_session):
    """Test GET /stream returns done event when no generation is happening."""
    from backend.app.models.interaction.conversation import Conversation

    conv = Conversation(user_id=1, title="Stream Conv")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    resp = client.get(f"/api/v1/conversations/{conv.id}/stream", headers=HEADERS)
    assert resp.status_code == 200

    body = resp.text
    lines = [line for line in body.strip().split("\n") if line.startswith("data: ")]
    assert len(lines) == 1

    chunk = json.loads(lines[0].removeprefix("data: "))
    assert chunk["type"] == "done"


def test_stream_receives_buffered_chunks(client, mock_auth, db_session):
    """Test GET /stream reads from an already-completed buffer."""
    from backend.app.models.interaction.conversation import Conversation
    from backend.app.services.interaction.stream_manager import stream_manager

    conv = Conversation(user_id=1, title="Buffer Conv")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    # Pre-populate a buffer with chunks and mark done
    buf = stream_manager.get_or_create_buffer(conv.id)
    buf.push(f"data: {json.dumps({'type': 'chunk', 'content': 'Hello ', 'tokens': 1})}\n\n")
    buf.push(f"data: {json.dumps({'type': 'chunk', 'content': 'world!', 'tokens': 2})}\n\n")
    buf.mark_done(final_data={"type": "done", "total_tokens": 2, "sources": []})

    resp = client.get(f"/api/v1/conversations/{conv.id}/stream", headers=HEADERS)
    assert resp.status_code == 200

    body = resp.text
    lines = [line for line in body.strip().split("\n") if line.startswith("data: ")]
    assert len(lines) >= 3  # 2 chunks + 1 done

    chunks = [json.loads(line.removeprefix("data: ")) for line in lines]
    chunk_types = [c["type"] for c in chunks]
    assert "chunk" in chunk_types
    assert "done" in chunk_types

    content = "".join(c["content"] for c in chunks if c["type"] == "chunk")
    assert content == "Hello world!"


def test_send_message_not_found(client, mock_auth):
    """Test POST returns 404 for nonexistent conversation."""
    resp = client.post(
        "/api/v1/conversations/99999/messages",
        json={"content": "Hi"},
        headers=HEADERS,
    )
    assert resp.status_code == 404
