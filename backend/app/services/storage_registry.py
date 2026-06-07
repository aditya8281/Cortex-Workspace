from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.storage_registry import StorageRegistry
from backend.app.core.storage_abstraction import validate_storage_path


def get_registry_for_user(db: Session, user_id: int) -> Optional[StorageRegistry]:
    return (
        db.query(StorageRegistry)
        .filter(StorageRegistry.user_id == user_id)
        .order_by(StorageRegistry.id.desc())
        .first()
    )


def register_user_storage(db: Session, user_id: int, storage_root: str) -> StorageRegistry:
    root = str(validate_storage_path(storage_root))
    entry = get_registry_for_user(db, user_id)
    if entry is None:
        entry = StorageRegistry(
            user_id=user_id,
            storage_root=root,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(entry)
    else:
        entry.storage_root = root
        entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)

    base = Path(root)
    for subdir in ("profile", "vault", "workspace", "exports", "memory_snapshots"):
        (base / subdir).mkdir(parents=True, exist_ok=True)

    return entry
