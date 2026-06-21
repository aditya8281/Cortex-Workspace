"""Add vault_locked column to users

Revision ID: c00000000003
Revises: b00000000002
Create Date: 2026-06-18
"""

import sqlalchemy as sa
from alembic import op

revision = "c00000000003"
down_revision = "b00000000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("vault_locked", sa.Boolean(), nullable=False, server_default=sa.text("true")))


def downgrade() -> None:
    op.drop_column("users", "vault_locked")
