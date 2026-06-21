from unittest.mock import MagicMock, patch

from backend.app.api.deps import get_current_user
from backend.app.main import app

HEADERS = {"Authorization": "Bearer fake-token"}


def _make_user(user_id: int):
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.username = f"user_{user_id}"
    mock_user.full_name = f"User {user_id}"
    mock_user.role = "user"
    mock_user.nickname = f"nick_{user_id}"
    mock_user.bio = None
    mock_user.description = None
    mock_user.profile_photo = None
    mock_user.handles_json = {}
    mock_user.preferences_json = {}
    mock_user.vault_locked = True
    mock_user.github_username = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.deleted_at = None
    return mock_user


def test_user_cannot_access_other_users_conversation(client, mock_auth, db_session):
    from backend.app.models.conversation import Conversation

    conv = Conversation(user_id=1, title="Private Conv")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    other_user = _make_user(99)
    app.dependency_overrides[get_current_user] = lambda: other_user

    resp = client.get(f"/api/v1/conversations/{conv.id}")
    assert resp.status_code == 404

    app.dependency_overrides[get_current_user] = lambda: mock_auth


def test_user_cannot_delete_other_users_conversation(client, mock_auth, db_session):
    from backend.app.models.conversation import Conversation

    conv = Conversation(user_id=1, title="Do Not Delete")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    other_user = _make_user(99)
    app.dependency_overrides[get_current_user] = lambda: other_user

    resp = client.delete(f"/api/v1/conversations/{conv.id}", headers=HEADERS)
    assert resp.status_code == 404

    app.dependency_overrides[get_current_user] = lambda: mock_auth


@patch("backend.app.services.rag_pipeline.get_rag_pipeline")
def test_user_cannot_send_message_to_other_users_conversation(mock_get_rag, client, mock_auth, db_session):
    from backend.app.models.conversation import Conversation

    conv = Conversation(user_id=1, title="Chat Private")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    rag_mock = MagicMock()
    rag_mock.retrieve_context.return_value = MagicMock(results=[], formatted_context="")
    mock_get_rag.return_value = rag_mock

    other_user = _make_user(99)
    app.dependency_overrides[get_current_user] = lambda: other_user

    resp = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={"content": "Hello"},
        headers=HEADERS,
    )
    assert resp.status_code == 404

    app.dependency_overrides[get_current_user] = lambda: mock_auth


def test_user_only_sees_own_conversations(client, mock_auth, db_session):
    from backend.app.models.conversation import Conversation

    for i in range(2):
        conv = Conversation(user_id=1, title=f"User1 Conv {i}")
        db_session.add(conv)

    other_user = _make_user(99)
    conv_other = Conversation(user_id=99, title="User99 Conv")
    db_session.add(conv_other)

    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: other_user
    resp99 = client.get("/api/v1/conversations")
    assert resp99.status_code == 200
    data99 = resp99.json()
    assert data99["total"] == 1
    assert data99["conversations"][0]["title"] == "User99 Conv"

    app.dependency_overrides[get_current_user] = lambda: mock_auth
    resp1 = client.get("/api/v1/conversations")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["total"] == 2
    titles = {c["title"] for c in data1["conversations"]}
    assert titles == {"User1 Conv 0", "User1 Conv 1"}
