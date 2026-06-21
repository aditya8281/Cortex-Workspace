"""Add ondelete clauses to FK constraints

Revision ID: f00000000006a
Revises: k00000000011
Create Date: 2026-06-20
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "f00000000006a"
down_revision = "k00000000011"
branch_labels = None
depends_on = None


def _get_existing_fk(bind, table: str, referred_table: str):
    """Find existing FK constraint name on a table referencing another table."""
    result = bind.execute(
        sa.text(
            "SELECT conname FROM pg_constraint "
            "JOIN pg_class ON pg_constraint.conrelid = pg_class.oid "
            "JOIN pg_class ref ON pg_constraint.confrelid = ref.oid "
            "WHERE pg_class.relname = :table "
            "AND ref.relname = :referred "
            "AND pg_constraint.contype = 'f'"
        ),
        {"table": table, "referred": referred_table},
    )
    row = result.fetchone()
    return row[0] if row else None


def _drop_and_recreate_fk(table: str, referred_table: str, cols, referred_cols, ondelete: str, fk_name: str):
    """Drop existing FK on a table referencing another (by any name) and recreate with ondelete."""
    bind = op.get_bind()
    existing = _get_existing_fk(bind, table, referred_table)
    if existing:
        op.drop_constraint(existing, table, type_="foreignkey")
    op.create_foreign_key(fk_name, table, referred_table, cols, referred_cols, ondelete=ondelete)


def upgrade() -> None:
    # notifications.user_id FK with ondelete CASCADE
    _drop_and_recreate_fk("notifications", "users", ["user_id"], ["id"], "CASCADE", "notifications_user_id_fkey")

    # repo_indexes.user_id FK with ondelete SET NULL
    _drop_and_recreate_fk("repo_indexes", "users", ["user_id"], ["id"], "SET NULL", "repo_indexes_user_id_fkey")

    # code_chunks.repo_id FK with ondelete CASCADE
    _drop_and_recreate_fk("code_chunks", "repo_indexes", ["repo_id"], ["id"], "CASCADE", "code_chunks_repo_id_fkey")


def downgrade() -> None:
    _drop_and_recreate_fk("notifications", "users", ["user_id"], ["id"], "NO ACTION", "notifications_user_id_fkey")
    _drop_and_recreate_fk("repo_indexes", "users", ["user_id"], ["id"], "NO ACTION", "repo_indexes_user_id_fkey")
    _drop_and_recreate_fk("code_chunks", "repo_indexes", ["repo_id"], ["id"], "NO ACTION", "code_chunks_repo_id_fkey")
