import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def mock_admin(db_session):
    from backend.app.api.deps import get_current_user
    from backend.app.core.security import hash_password
    from backend.app.main import app
    from backend.app.models.interaction.user import User

    admin = User(
        username="admin_user",
        full_name="Admin User",
        hashed_password=hash_password("password123"),
        role="admin",
        nickname="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    admin_id = admin.id

    def _override():
        return db_session.query(User).filter(User.id == admin_id).first()

    app.dependency_overrides[get_current_user] = _override
    yield admin
    app.dependency_overrides.pop(get_current_user, None)


def _create_test_user(db_session):
    from backend.app.core.security import hash_password
    from backend.app.models.interaction.user import User

    user = User(
        username="target_user",
        full_name="Target User",
        hashed_password=hash_password("password123"),
        role="user",
        nickname="target",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_list_users(client, mock_admin, db_session):
    _create_test_user(db_session)
    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_user(client, mock_admin, db_session):
    user = _create_test_user(db_session)
    resp = client.get(f"/api/v1/users/{user.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "target_user"


def test_get_user_not_found(client, mock_admin):
    resp = client.get("/api/v1/users/99999")
    assert resp.status_code == 404


def test_promote_user(client, mock_admin, db_session):
    user = _create_test_user(db_session)
    resp = client.post(f"/api/v1/users/{user.id}/promote", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


def test_demote_user(client, mock_admin, db_session):
    user = _create_test_user(db_session)
    client.post(f"/api/v1/users/{user.id}/promote", headers=HEADERS)
    resp = client.post(f"/api/v1/users/{user.id}/demote", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "user"


def test_demote_nonexistent_user(client, mock_admin):
    resp = client.post("/api/v1/users/99999/demote", headers=HEADERS)
    assert resp.status_code == 404


def test_non_admin_forbidden(client, mock_auth):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 403
