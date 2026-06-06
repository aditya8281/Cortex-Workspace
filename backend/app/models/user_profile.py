from __future__ import annotations

import json
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_photo: Mapped[str | None] = mapped_column(String, nullable=True)
    handles_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="public")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", backref="profile", uselist=False)

    @property
    def handles(self) -> dict:
        try:
            return json.loads(self.handles_json)
        except Exception:
            return {}

    @handles.setter
    def handles(self, val: dict) -> None:
        self.handles_json = json.dumps(val or {})


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    prefs_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    @property
    def prefs(self) -> dict:
        try:
            return json.loads(self.prefs_json)
        except Exception:
            return {}

    @prefs.setter
    def prefs(self, val: dict) -> None:
        self.prefs_json = json.dumps(val or {})


class ProfileAudit(Base):
    __tablename__ = "profile_audit"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    field: Mapped[str] = mapped_column(String(128), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
