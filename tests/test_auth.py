import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.models.user import User  # noqa: F401
from backend.app.api.deps import get_db


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    # Each test gets its own isolated database file via pytest tmp_path
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(name="client", scope="function")
def fixture_client(tmp_path):
    # Each test client gets its own completely isolated database
    db_file = tmp_path / "client_test.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_create_user(client):
    # Pre-populate a dummy first user so that the created user gets "user" role
    dummy_payload = {
        "email": "dummyadmin@example.com",
        "full_name": "Dummy Admin",
        "password": "securepassword123"
    }
    client.post("/api/v1/users", json=dummy_payload)

    payload = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert data["role"] == "user"


def test_create_duplicate_user(client):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Test User 1",
        "password": "password123"
    }
    # First creation
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 200

    # Second creation (should fail cleanly with 400 instead of crashing with 500)
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_and_me(client):
    # 1. Register a user
    register_payload = {
        "email": "me@example.com",
        "full_name": "Me User",
        "password": "mypassword"
    }
    client.post("/api/v1/users", json=register_payload)

    # 2. Login
    login_payload = {
        "email": "me@example.com",
        "password": "mypassword"
    }
    response = client.post("/api/v1/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Access protected profile /me with valid token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == "me@example.com"
    assert profile_data["full_name"] == "Me User"

    # 4. Access protected profile /me with invalid token
    bad_headers = {"Authorization": "Bearer badtoken"}
    response = client.get("/api/v1/me", headers=bad_headers)
    assert response.status_code == 401
