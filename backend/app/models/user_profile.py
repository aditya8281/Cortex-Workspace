from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    goals_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    focus_areas_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    languages_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
