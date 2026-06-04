from datetime import datetime
from sqlalchemy import Integer, String, LargeBinary, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    api_key_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    api_base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
    vector_db: Mapped[str | None] = mapped_column(String, nullable=True)
    inference_engine: Mapped[str | None] = mapped_column(String, nullable=True)
    code_parsing: Mapped[str | None] = mapped_column(String, nullable=True)
    selected_model: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
