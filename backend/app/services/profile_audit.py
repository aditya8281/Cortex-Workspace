from __future__ import annotations

from datetime import datetime
from backend.app.models.user_profile import ProfileAudit


def record_profile_audit(db, user_id: int, field: str, old_value, new_value, ip: str | None = None):
    try:
        pa = ProfileAudit(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            field=field,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            ip_address=ip,
        )
        db.add(pa)
        db.commit()
    except Exception:
        db.rollback()
