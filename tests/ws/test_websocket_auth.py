"""WebSocket authentication tests — all WS endpoints reject unauthenticated connections."""

import pytest

from backend.app.core.security import create_access_token


def _make_token(user_id: int = 1) -> str:
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
def test_ws_rejects_no_token(client, path: str):
    """Every WS endpoint must send an error when no token is provided."""
    with client.websocket_connect(path) as ws:
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
def test_ws_rejects_bad_token(client, path: str):
    """Every WS endpoint must send an error for a garbage token."""
    with client.websocket_connect(
        path, headers={"sec-websocket-protocol": "garbage-token"}
    ) as ws:
        msg = ws.receive_json()
    assert msg.get("type") == "error"
    assert "message" in msg


def test_ws_demo_echo(client):
    """Demo echo action responds with the same text."""
    token = _make_token()
    with client.websocket_connect(
        "/ws/demo", headers={"sec-websocket-protocol": token}
    ) as ws:
        ws.send_json({"action": "echo", "text": "hello world"})
        resp = ws.receive_json()
        assert resp == {"action": "echo", "data": "hello world"}


def test_ws_demo_stream(client):
    """Demo stream action emits chunks ending with done=True."""
    token = _make_token()
    with client.websocket_connect(
        "/ws/demo", headers={"sec-websocket-protocol": token}
    ) as ws:
        ws.send_json({"action": "stream", "text": "a b c"})
        chunks = []
        while True:
            msg = ws.receive_json()
            chunks.append(msg)
            if msg.get("done"):
                break
        assert len(chunks) >= 3
        assert chunks[-1]["done"] is True
        assert chunks[-1]["chunk"] == ""


def test_ws_demo_unknown_action(client):
    """Demo responds with error for unknown actions."""
    token = _make_token()
    with client.websocket_connect(
        "/ws/demo", headers={"sec-websocket-protocol": token}
    ) as ws:
        ws.send_json({"action": "nonexistent"})
        resp = ws.receive_json()
        assert resp["action"] == "error"
        assert "Unknown action" in resp["message"]
