from datetime import datetime
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StorageRegistry(Base):
    __tablename__ = "user_storage_registry"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    storage_root: Mapped[str] = mapped_column(String, nullable=False)
    profile_path: Mapped[str | None] = mapped_column(String, nullable=True)
    vault_path: Mapped[str | None] = mapped_column(String, nullable=True)
    exports_path: Mapped[str | None] = mapped_column(String, nullable=True)
    activity_path: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
