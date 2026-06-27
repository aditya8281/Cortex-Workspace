from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def log_event(
    event_type: str,
    user_id: int | None,
    ip: str | None,
    metadata: dict[str, Any] | None = None,
    *,
    db: Session | None = None,
):
    """
    Record an auth audit event.

    If *db* is provided the event is written using the request's existing
    session (no new connection opened).  Otherwise a one-off session is
    created and immediately closed — this avoids connection leaks while
    remaining backward-compatible with call-sites that don't pass *db*.
    """
    owns_db = False
    if db is None:
        from backend.app.db.session import SessionLocal

        db = SessionLocal()
        owns_db = True
    try:
        from backend.app.models.privacy.auth_event import AuthEvent

        ev = AuthEvent(
            user_id=user_id,
            ip_address=ip,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            metadata_json=json.dumps(metadata or {}),
        )
        db.add(ev)
        db.commit()
    except Exception as exc:
        logger.warning("Audit log_event failed: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        if owns_db:
            try:
                db.close()
            except Exception:
                pass
