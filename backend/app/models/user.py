from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(String, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    role: Mapped[str] = mapped_column(String, default="user", nullable=False)

    nickname: Mapped[str] = mapped_column(String, nullable=False, default="")
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_photo: Mapped[str | None] = mapped_column(String, nullable=True)
    handles_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    vault_password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    vault_locked: Mapped[bool] = mapped_column(default=True, nullable=False)
    preferences_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    github_username: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    github_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    programming_languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    frameworks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    current_projects: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    contribution_style: Mapped[str | None] = mapped_column(String(32), nullable=True)
    social_links: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def handles(self) -> dict:
        if isinstance(self.handles_json, dict):
            return self.handles_json
        return {}

    @handles.setter
    def handles(self, val: dict) -> None:
        self.handles_json = val or {}

    @property
    def preferences(self) -> dict:
        if isinstance(self.preferences_json, dict):
            return self.preferences_json
        return {}

    @preferences.setter
    def preferences(self, val: dict) -> None:
        self.preferences_json = val or {}
