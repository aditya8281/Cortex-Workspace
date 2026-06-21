from unittest.mock import MagicMock, patch

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


def test_list_notifications_empty(client, mock_auth):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["notifications"] == []
    assert data["total"] == 0
    assert data["unread_count"] == 0


def test_mark_notification_read(client, mock_auth, db_session):
    from backend.app.models.notification import Notification

    notif = Notification(user_id=1, type="system", title="Test", message="Hello", read=False)
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    resp = client.post(f"/api/v1/notifications/{notif.id}/read", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_mark_notification_read_not_found(client, mock_auth):
    resp = client.post("/api/v1/notifications/99999/read", headers=HEADERS)
    assert resp.status_code == 404


def test_mark_all_read(client, mock_auth, db_session):
    from backend.app.models.notification import Notification

    for i in range(3):
        db_session.add(Notification(user_id=1, type="system", title=f"N{i}", message="m", read=False))
    db_session.commit()

    resp = client.post("/api/v1/notifications/read-all", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["marked_read"] == 3


def test_delete_notification(client, mock_auth, db_session):
    from backend.app.models.notification import Notification

    notif = Notification(user_id=1, type="system", title="Del", message="x", read=False)
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    resp = client.delete(f"/api/v1/notifications/{notif.id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_delete_notification_not_found(client, mock_auth):
    resp = client.delete("/api/v1/notifications/99999", headers=HEADERS)
    assert resp.status_code == 404
