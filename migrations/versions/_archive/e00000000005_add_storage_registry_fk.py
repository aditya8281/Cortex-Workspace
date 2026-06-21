"""Add FK constraint on user_storage_registry.user_id.

Revision ID: e00000000005
Revises: d00000000004
Create Date: 2026-06-19
"""

from alembic import op

revision = "e00000000005"
down_revision = "d00000000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        # Clean up orphaned rows before adding FK constraint
        op.execute(
            "DELETE FROM user_storage_registry "
            "WHERE user_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM users WHERE users.id = user_storage_registry.user_id)"
        )
        op.create_foreign_key(
            "fk_storage_registry_user_id",
            "user_storage_registry",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint("fk_storage_registry_user_id", "user_storage_registry", type_="foreignkey")
