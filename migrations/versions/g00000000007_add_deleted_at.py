"""Add deleted_at column to users for soft delete.

Revision ID: g00000000007
Revises: f00000000006
Create Date: 2026-06-19
"""
import sqlalchemy as sa
from alembic import op

revision = "g00000000007"
down_revision = "f00000000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
