from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.storage_registry import StorageRegistry


def get_registry_for_user(db: Session, user_id: int) -> StorageRegistry | None:
    return (
        db.query(StorageRegistry)
        .filter(StorageRegistry.user_id == user_id)
        .order_by(StorageRegistry.id.desc())
        .first()
    )


def register_user_storage(db: Session, user_id: int, storage_root: str) -> StorageRegistry:
    entry = get_registry_for_user(db, user_id)
    if entry is None:
        entry = StorageRegistry(
            user_id=user_id,
            storage_root=storage_root,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(entry)
    else:
        entry.storage_root = storage_root
        entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)

    base = Path(storage_root)
    for subdir in ("profile", "vault", "workspace", "exports", "memory_snapshots"):
        (base / subdir).mkdir(parents=True, exist_ok=True)

    return entry
