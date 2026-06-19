"""baseline — create the canonical Cortex schema (auth + memory only).

Revision ID: a00000000001
Revises:
Create Date: 2026-06-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a00000000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ───────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("nickname", sa.String(), nullable=False, server_default=""),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("profile_photo", sa.String(), nullable=True),
        sa.Column("handles_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("vault_password_hash", sa.String(), nullable=True),
        sa.Column("preferences_json", sa.Text(), nullable=False, server_default="{}"),
    )

    # ── auth_events ─────────────────────────────────────────────────
    op.create_table(
        "auth_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
    )

    # ── knowledge_entries ───────────────────────────────────────────
    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("category", sa.String(64), nullable=False, index=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_path", sa.String(1024), nullable=True, index=True),
        sa.Column("source_key", sa.String(512), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── user_storage_registry ───────────────────────────────────────
    op.create_table(
        "user_storage_registry",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("storage_root", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_storage_registry")
    op.drop_table("knowledge_entries")
    op.drop_table("auth_events")
    op.drop_table("users")
