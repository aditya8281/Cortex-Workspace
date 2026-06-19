"""Fix schema consistency issues:

- Add unique constraint on github_username (model has it, migration b missed it)
- Add server_default on user_storage_registry.created_at / updated_at
- Add server_default on auth_events.timestamp

Revision ID: h00000000008
Revises: g00000000007
Create Date: 2026-06-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h00000000008"
down_revision: str | None = "g00000000007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # ── 1. Add unique constraint on github_username ──────────────────────
    # Model declares unique=True but migration b00000000002 omitted it.
    # Safe to add only when no duplicates exist (will fail if duplicates found).
    if not is_sqlite:
        op.create_unique_constraint("uq_users_github_username", "users", ["github_username"])

    # ── 2. Add server_default on user_storage_registry timestamps ────────
    # Columns are NOT NULL but have no server_default — raw SQL inserts fail.
    if not is_sqlite:
        op.alter_column(
            "user_storage_registry", "created_at",
            server_default=sa.text("LOCALTIMESTAMP"),
        )
        op.alter_column(
            "user_storage_registry", "updated_at",
            server_default=sa.text("LOCALTIMESTAMP"),
        )

    # ── 3. Add server_default on auth_events.timestamp ───────────────────
    if not is_sqlite:
        op.alter_column(
            "auth_events", "timestamp",
            server_default=sa.text("LOCALTIMESTAMP"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if not is_sqlite:
        op.drop_constraint("uq_users_github_username", "users", type_="unique")

    if not is_sqlite:
        op.alter_column("user_storage_registry", "created_at", server_default=None)
        op.alter_column("user_storage_registry", "updated_at", server_default=None)

    if not is_sqlite:
        op.alter_column("auth_events", "timestamp", server_default=None)
