from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.db.session import SessionLocal
from backend.app.models.auth_event import AuthEvent


def log_event(event_type: str, user_id: int | None, ip: str | None, metadata: dict[str, Any] | None = None):
    db = SessionLocal()
    try:
        ev = AuthEvent(
            user_id=user_id,
            ip_address=ip,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            metadata_json=metadata or {},
        )
        db.add(ev)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
