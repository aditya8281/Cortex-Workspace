"""add username to users

Revision ID: 0a1b2c3d4e5f
Revises: e4834d8614aa
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "e4834d8614aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(), nullable=True))
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, email FROM users")).fetchall()
    for row in rows:
        email = row.email or "user"
        local_part = (email.split("@", 1)[0] or "user").strip().lower()
        username = f"{local_part}_{row.id}"
        bind.execute(
            sa.text("UPDATE users SET username = :username WHERE id = :id"),
            {"username": username, "id": row.id},
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "username")
