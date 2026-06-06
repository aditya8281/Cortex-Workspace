from typing import Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.storage_registry import StorageRegistry


def get_registry_for_user(db: Session, user_id: int) -> Optional[StorageRegistry]:
    return db.query(StorageRegistry).filter(StorageRegistry.user_id == user_id).order_by(StorageRegistry.id.desc()).first()


def register_user_storage(db: Session, user_id: int, storage_root: str, profile_path: Optional[str] = None, vault_path: Optional[str] = None, exports_path: Optional[str] = None, activity_path: Optional[str] = None) -> StorageRegistry:
    root = str(Path(storage_root).expanduser().resolve())
    profile_p = profile_path or str(Path(root) / "profile")
    vault_p = vault_path or str(Path(root) / "vault")
    exports_p = exports_path or str(Path(root) / "exports")
    activity_p = activity_path or str(Path(root) / "activity")

    entry = StorageRegistry(
        user_id=user_id,
        storage_root=root,
        profile_path=profile_p,
        vault_path=vault_p,
        exports_path=exports_p,
        activity_path=activity_p,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
