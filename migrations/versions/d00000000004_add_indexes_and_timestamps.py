"""Add missing indexes, timestamps, and FK constraint.

Revision ID: d00000000004
Revises: c00000000003
Create Date: 2026-06-18
"""
import sqlalchemy as sa
from alembic import op

revision = "d00000000004"
down_revision = "c00000000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw SQL with IF NOT EXISTS to avoid conflicts when tests
    # run create_all() before migrations.
    op.execute("CREATE INDEX IF NOT EXISTS ix_auth_events_user_id ON auth_events (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auth_events_event_type ON auth_events (event_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_auth_events_timestamp ON auth_events (timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_entries_user_category ON knowledge_entries (user_id, category)")

    # user_storage_registry: unique index on user_id (safe — one storage root per user)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_storage_registry_user_id ON user_storage_registry (user_id)")

    # Timestamps for users
    op.add_column("users", sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))

    # FK constraint on auth_events.user_id
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_auth_events_user_id",
            "auth_events",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint("fk_auth_events_user_id", "auth_events", type_="foreignkey")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "created_at")
    op.execute("DROP INDEX IF EXISTS ix_user_storage_registry_user_id")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_entries_user_category")
    op.execute("DROP INDEX IF EXISTS ix_auth_events_timestamp")
    op.execute("DROP INDEX IF EXISTS ix_auth_events_event_type")
    op.execute("DROP INDEX IF EXISTS ix_auth_events_user_id")
