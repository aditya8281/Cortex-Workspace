from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserModelSettings(Base):
    __tablename__ = "user_model_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    inference_backend: Mapped[str] = mapped_column(String(50), default="auto", nullable=False)
    huggingface_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auto_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_concurrent_downloads: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
