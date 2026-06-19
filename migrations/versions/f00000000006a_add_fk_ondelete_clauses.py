"""Add ondelete clauses to FK constraints

Revision ID: f00000000006a
Revises: f00000000006
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "f00000000006a"
down_revision = "f00000000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop and recreate notification.user_id FK with ondelete CASCADE
    op.drop_constraint("notifications_user_id_fkey", "notifications", type_="foreignkey")
    op.create_foreign_key(
        "notifications_user_id_fkey",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop and recreate repo_indexes.user_id FK with ondelete SET NULL
    op.drop_constraint("repo_indexes_user_id_fkey", "repo_indexes", type_="foreignkey")
    op.create_foreign_key(
        "repo_indexes_user_id_fkey",
        "repo_indexes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Drop and recreate code_chunks.repo_id FK with ondelete CASCADE
    op.drop_constraint("code_chunks_repo_id_fkey", "code_chunks", type_="foreignkey")
    op.create_foreign_key(
        "code_chunks_repo_id_fkey",
        "code_chunks",
        "repo_indexes",
        ["repo_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Revert to original FKs without ondelete
    op.drop_constraint("notifications_user_id_fkey", "notifications", type_="foreignkey")
    op.create_foreign_key(
        "notifications_user_id_fkey",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("repo_indexes_user_id_fkey", "repo_indexes", type_="foreignkey")
    op.create_foreign_key(
        "repo_indexes_user_id_fkey",
        "repo_indexes",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("code_chunks_repo_id_fkey", "code_chunks", type_="foreignkey")
    op.create_foreign_key(
        "code_chunks_repo_id_fkey",
        "code_chunks",
        "repo_indexes",
        ["repo_id"],
        ["id"],
    )
