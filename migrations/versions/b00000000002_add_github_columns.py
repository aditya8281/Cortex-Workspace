"""Add github columns to users

Revision ID: b00000000002
Revises: a00000000001
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa

revision = "b00000000002"
down_revision = "a00000000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite doesn't support ALTER TABLE ... ADD CONSTRAINT, so we add
    # the columns without the unique constraint at the DB level.
    # The application layer enforces uniqueness via the ORM unique=True.
    op.add_column("users", sa.Column("github_username", sa.String(), nullable=True))
    op.add_column("users", sa.Column("github_token_encrypted", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "github_token_encrypted")
    op.drop_column("users", "github_username")
