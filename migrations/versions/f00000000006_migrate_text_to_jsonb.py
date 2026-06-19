"""Migrate Text JSON columns to JSONB.

- Must drop server_default before altering type (PG can't auto-cast text default to jsonb)
- Re-add JSONB-compatible default after conversion

Revision ID: f00000000006
Revises: e00000000005
Create Date: 2026-06-19
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "f00000000006"
down_revision = "e00000000005"
branch_labels = None
depends_on = None

_TABLES = [
    ("users", "handles_json"),
    ("users", "preferences_json"),
    ("auth_events", "metadata_json"),
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        for table, column in _TABLES:
            # Drop default before type change — PG cannot auto-cast text default to jsonb
            op.alter_column(table, column, server_default=None)
            op.alter_column(table, column, type_=JSONB, postgresql_using=f"{column}::jsonb")
            # Re-add default as valid JSONB
            op.alter_column(table, column, server_default=sa.text("'{}'::jsonb"))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        for table, column in reversed(_TABLES):
            op.alter_column(table, column, server_default=None)
            op.alter_column(table, column, type_=sa.Text())
            op.alter_column(table, column, server_default=sa.text("'{}'"))
