from datetime import datetime
from pathlib import Path
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StorageRegistry(Base):
    __tablename__ = "user_storage_registry"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    storage_root: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def profile_path(self) -> str:
        return str((Path(self.storage_root) / "profile").resolve())

    @property
    def vault_path(self) -> str:
        return str((Path(self.storage_root) / "vault").resolve())

    @property
    def exports_path(self) -> str:
        return str((Path(self.storage_root) / "exports").resolve())

    @property
    def workspace_path(self) -> str:
        return str((Path(self.storage_root) / "workspace").resolve())

    @property
    def memory_snapshots_path(self) -> str:
        return str((Path(self.storage_root) / "memory_snapshots").resolve())
