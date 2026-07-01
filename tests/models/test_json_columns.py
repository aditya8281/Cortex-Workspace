"""Tests for JSON column handling — SQLite compatibility and serialization."""

from __future__ import annotations

from backend.app.models.interaction.user import User


def test_json_roundtrip(client):
    """Verify JSON columns store and retrieve dict values correctly."""
    payload = {
        "username": "json_rt_user",
        "full_name": "JSON RT",
        "nickname": "jsonrt",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "vault_password": "VaultPass123!",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200
    user_id = resp.json()["user"]["id"]

    from backend.app.api.deps import get_db
    from backend.app.main import app

    db_func = app.dependency_overrides.get(get_db, get_db)
    db = next(db_func())

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user is not None

        user.handles = {"github": "testuser", "twitter": "@test"}
        user.preferences = {"theme": "dark", "notifications": {"email": True}}
        db.flush()
        db.refresh(user)

        assert user.handles == {"github": "testuser", "twitter": "@test"}
        assert user.handles["github"] == "testuser"
        assert user.preferences == {"theme": "dark", "notifications": {"email": True}}
        assert user.preferences["theme"] == "dark"
        assert user.preferences["notifications"]["email"] is True

        user.handles = {}
        user.preferences = {}
        db.flush()
    finally:
        db.close()


def test_json_filter_by_key(client):
    """Verify JSON columns can be filtered by key path."""
    payload = {
        "username": "json_filter_user",
        "full_name": "JSON Filter",
        "nickname": "jsonfilter",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "vault_password": "VaultPass123!",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200
    user_id = resp.json()["user"]["id"]

    from backend.app.api.deps import get_db
    from backend.app.main import app

    db_func = app.dependency_overrides.get(get_db, get_db)
    db = next(db_func())

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user is not None

        user.handles = {"github": "json-filter-test", "twitter": "@jft"}
        db.flush()

        result = db.query(User).filter(User.handles_json["github"].as_string() == "json-filter-test").first()
        assert result is not None

        user.handles = {}
        db.flush()
    finally:
        db.close()


def test_json_property_getter_setter_on_new_user(client):
    """Verify JSON property getter/setter works on newly created users."""
    payload = {
        "username": "jsonb_prop_user",
        "full_name": "JSONB Test",
        "nickname": "jsonbtest",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "vault_password": "VaultPass123!",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200

    from backend.app.api.deps import get_db
    from backend.app.main import app

    db_func = app.dependency_overrides.get(get_db, get_db)
    db = next(db_func())
    try:
        user = db.query(User).filter(User.username == "jsonb_prop_user").first()
        assert user is not None

        user.handles = {"custom": "data"}
        user.preferences = {"lang": "en"}
        db.flush()
        db.refresh(user)

        assert user.handles == {"custom": "data"}
        assert user.preferences == {"lang": "en"}
    finally:
        db.close()
