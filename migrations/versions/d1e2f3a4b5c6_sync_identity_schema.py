"""sync identity schema with current auth/profile services

Revision ID: d1e2f3a4b5c6
Revises: b2c3d4e5f6a8
Create Date: 2026-06-07 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_columns(inspector: sa.engine.reflection.Inspector, table_name: str) -> set[str]:
    try:
        return {column["name"] for column in inspector.get_columns(table_name)}
    except Exception:
        return set()


def _table_names(inspector: sa.engine.reflection.Inspector) -> set[str]:
    try:
        return set(inspector.get_table_names())
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = _table_names(inspector)
    user_columns = _table_columns(inspector, "users")

    if "data_path" not in user_columns:
        op.add_column("users", sa.Column("data_path", sa.String(length=512), nullable=True))
        inspector = sa.inspect(bind)
        user_columns = _table_columns(inspector, "users")

    if "data_path" in user_columns and "personal_storage_path" in user_columns:
        bind.execute(
            sa.text(
                """
                UPDATE users
                SET data_path = COALESCE(data_path, personal_storage_path)
                WHERE data_path IS NULL AND personal_storage_path IS NOT NULL
                """
            )
        )

    if "user_profiles" not in tables:
        op.create_table(
            "user_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("nickname", sa.String(length=64), nullable=True),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("profile_photo", sa.String(), nullable=True),
            sa.Column("handles_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("visibility", sa.String(length=32), nullable=False, server_default="public"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        )
        op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)
        tables.add("user_profiles")

    if "user_preferences" not in tables:
        op.create_table(
            "user_preferences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("prefs_json", sa.Text(), nullable=False, server_default="{}"),
        )
        op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)
        tables.add("user_preferences")

    if "profile_audit" not in tables:
        op.create_table(
            "profile_audit",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
            sa.Column("field", sa.String(length=128), nullable=False),
            sa.Column("old_value", sa.Text(), nullable=True),
            sa.Column("new_value", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=64), nullable=True),
        )
        op.create_index("ix_profile_audit_user_id", "profile_audit", ["user_id"], unique=False)
        op.create_index("ix_profile_audit_timestamp", "profile_audit", ["timestamp"], unique=False)
        tables.add("profile_audit")

    if "auth_events" not in tables:
        op.create_table(
            "auth_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("ip_address", sa.String(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        )
        op.create_index("ix_auth_events_user_id", "auth_events", ["user_id"], unique=False)
        op.create_index("ix_auth_events_timestamp", "auth_events", ["timestamp"], unique=False)
        tables.add("auth_events")

    # Backfill identity profile rows from users for existing deployments.
    user_rows = bind.execute(
        sa.text(
            """
            SELECT id, full_name, username, nickname, bio, description, profile_photo, handles_json, preferences_json
            FROM users
            """
        )
    ).fetchall()

    existing_profile_user_ids = set()
    if "user_profiles" in tables:
        existing_profile_user_ids = {
            row[0] for row in bind.execute(sa.text("SELECT user_id FROM user_profiles")).fetchall()
        }

    for row in user_rows:
        if row.id not in existing_profile_user_ids:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO user_profiles (
                        user_id, full_name, nickname, bio, description, profile_photo, handles_json, visibility, updated_at
                    ) VALUES (
                        :user_id, :full_name, :nickname, :bio, :description, :profile_photo, :handles_json, :visibility, CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "user_id": row.id,
                    "full_name": row.full_name,
                    "nickname": (row.nickname or row.username or row.full_name or ""),
                    "bio": row.bio,
                    "description": row.description,
                    "profile_photo": row.profile_photo,
                    "handles_json": row.handles_json or "{}",
                    "visibility": "public",
                },
            )

    existing_pref_user_ids = set()
    if "user_preferences" in tables:
        existing_pref_user_ids = {
            row[0] for row in bind.execute(sa.text("SELECT user_id FROM user_preferences")).fetchall()
        }

    for row in user_rows:
        if row.id not in existing_pref_user_ids:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO user_preferences (user_id, prefs_json)
                    VALUES (:user_id, :prefs_json)
                    """
                ),
                {
                    "user_id": row.id,
                    "prefs_json": row.preferences_json or "{}",
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = _table_names(inspector)

    if "auth_events" in tables:
        op.drop_index("ix_auth_events_timestamp", table_name="auth_events")
        op.drop_index("ix_auth_events_user_id", table_name="auth_events")
        op.drop_table("auth_events")

    if "profile_audit" in tables:
        op.drop_index("ix_profile_audit_timestamp", table_name="profile_audit")
        op.drop_index("ix_profile_audit_user_id", table_name="profile_audit")
        op.drop_table("profile_audit")

    if "user_preferences" in tables:
        op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
        op.drop_table("user_preferences")

    if "user_profiles" in tables:
        op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
        op.drop_table("user_profiles")

    user_columns = _table_columns(inspector, "users")
    if "data_path" in user_columns:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("data_path")
