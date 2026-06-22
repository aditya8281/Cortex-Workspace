"""Add index on users.deleted_at for soft-delete queries.

Revision ID: c00000000002
Revises: c00000000001
Create Date: 2026-06-22 00:00:00.000000
"""

from alembic import op

revision = "c00000000002"
down_revision = "c00000000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_users_deleted_at", table_name="users")
