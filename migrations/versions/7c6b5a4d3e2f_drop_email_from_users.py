"""drop email from users

Revision ID: 7c6b5a4d3e2f
Revises: 8f9e7d6c5b4a
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c6b5a4d3e2f"
down_revision: Union[str, Sequence[str], None] = "8f9e7d6c5b4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("email")
    else:
        op.drop_column("users", "email")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(sa.Column("email", sa.String(), nullable=False))
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    else:
        op.add_column("users", sa.Column("email", sa.String(), nullable=False))
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
