"""WebSocket security tests — expired tokens and non-existent users."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from jose import jwt

from backend.app.core.config import settings
from backend.app.core.security import create_access_token


def _expired_token() -> str:
    """Create a token that has already expired."""
    payload = {
        "sub": "1",
        "jti": str(uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _valid_token(user_id: int = 1) -> str:
    return create_access_token({"sub": str(user_id)})


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/ws/system",
        "/api/v1/ws/agents",
        "/api/v1/ws/chat",
        "/api/v1/ws/models",
        "/api/v1/ws/notifications",
        "/ws/demo",
    ],
)
def test_ws_rejects_expired_token(client, path: str):
    """Expired JWT is rejected by all WS endpoints."""
    token = _expired_token()
    with client.websocket_connect(path, headers={"sec-websocket-protocol": token}) as ws:
        msg = ws.receive_json()
    assert msg.get("type") == "error"
    assert "message" in msg


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/ws/system",
        "/api/v1/ws/agents",
        "/api/v1/ws/chat",
        "/api/v1/ws/models",
        "/api/v1/ws/notifications",
        "/ws/demo",
    ],
)
def test_ws_rejects_nonexistent_user(client, path: str):
    """Token for a user that doesn't exist is rejected by all WS endpoints.

    verify_ws_token() queries PostgreSQL for user.id=99999 (no deleted_at).
    Since that user doesn't exist, the check::
        user = db.query(User).filter(User.id == int(user_id), User.deleted_at.is_(None)).first()
    returns None → Exception raised.
    """
    token = _valid_token(user_id=99999)
    with client.websocket_connect(path, headers={"sec-websocket-protocol": token}) as ws:
        msg = ws.receive_json()
    assert msg.get("type") == "error"
    assert "message" in msg
