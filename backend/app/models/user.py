import json
from sqlalchemy import String, Text
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
    handles_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    vault_password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    preferences_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    @property
    def handles(self) -> dict:
        try:
            return json.loads(self.handles_json)
        except Exception:
            return {}

    @handles.setter
    def handles(self, val: dict) -> None:
        self.handles_json = json.dumps(val or {})

    @property
    def preferences(self) -> dict:
        try:
            return json.loads(self.preferences_json)
        except Exception:
            return {}

    @preferences.setter
    def preferences(self, val: dict) -> None:
        self.preferences_json = json.dumps(val or {})
