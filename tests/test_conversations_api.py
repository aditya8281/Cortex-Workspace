import json
from unittest.mock import MagicMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


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
    from backend.app.models.conversation import Conversation

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
    from backend.app.models.conversation import Conversation

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


@patch("backend.app.services.rag_pipeline.get_rag_pipeline")
@patch("backend.app.services.llm.manager.llm_manager")
def test_send_message(mock_llm, mock_get_rag, client, mock_auth, db_session):
    from backend.app.models.conversation import Conversation

    conv = Conversation(user_id=1, title="Chat Conv")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    rag_mock = MagicMock()
    rag_mock.retrieve_context.return_value = MagicMock(results=[], formatted_context="")
    mock_get_rag.return_value = rag_mock

    async def fake_stream(messages, **kwargs):
        yield "Hello "
        yield "world!"

    mock_llm.chat_stream = fake_stream

    resp = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={"content": "Hi there"},
        headers=HEADERS,
    )
    assert resp.status_code == 200

    body = resp.text
    lines = [line for line in body.strip().split("\n") if line.startswith("data: ")]
    assert len(lines) >= 2

    chunks = [json.loads(line.removeprefix("data: ")) for line in lines]
    chunk_types = [c["type"] for c in chunks]
    assert "chunk" in chunk_types
    assert "done" in chunk_types

    content = "".join(c["content"] for c in chunks if c["type"] == "chunk")
    assert content == "Hello world!"
