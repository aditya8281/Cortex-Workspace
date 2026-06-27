"""Role and permission models — RBAC foundation for access control."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

# Association tables (no FK constraints for SQLite compatibility — use explicit joins)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, primary_key=True),
    Column("role_id", Integer, primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, primary_key=True),
    Column("permission_id", Integer, primary_key=True),
)


class Role(Base):
    """Named role that groups permissions."""

    __tablename__ = "privacy_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        primaryjoin="Role.id == role_permissions.c.role_id",
        secondaryjoin="Permission.id == role_permissions.c.permission_id",
        backref="roles",
    )


class Permission(Base):
    """Resource-action permission pair."""

    __tablename__ = "privacy_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
