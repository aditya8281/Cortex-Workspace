"""cortex identity refactor

Revision ID: b2c3d4e5f6a8
Revises: b1c2d3e4f6a7
Create Date: 2026-06-06 18:45:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a8"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column("users", sa.Column("nickname", sa.String(length=256), nullable=False, server_default=""))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("profile_photo", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("handles_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("users", sa.Column("vault_password_hash", sa.String(length=256), nullable=True))
    op.add_column("users", sa.Column("personal_storage_path", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("preferences_json", sa.Text(), nullable=False, server_default="{}"))

    # Data migration from user_profiles to users
    connection = op.get_bind()
    metadata = sa.MetaData()
    user_profiles = sa.Table(
        "user_profiles",
        metadata,
        sa.Column("user_id", sa.Integer()),
        sa.Column("display_name", sa.String()),
        sa.Column("bio", sa.Text()),
    )
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("full_name", sa.String()),
        sa.Column("username", sa.String()),
    )
    
    inspector = sa.inspect(connection)
    if "user_profiles" in inspector.get_table_names():
        profiles = connection.execute(sa.select(user_profiles.c.user_id, user_profiles.c.display_name, user_profiles.c.bio)).fetchall()
        for user_id, display_name, bio in profiles:
            user_row = connection.execute(sa.select(users.c.full_name, users.c.username).where(users.c.id == user_id)).fetchone()
            fallback_nickname = ""
            if user_row:
                fallback_nickname = user_row[0] or user_row[1] or ""
            
            nickname_val = display_name if display_name else fallback_nickname
            connection.execute(
                sa.update(users)
                .where(users.c.id == user_id)
                .values(nickname=nickname_val, bio=bio)
            )

    # Drop user_profiles index & table
    if "user_profiles" in inspector.get_table_names():
        op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
        op.drop_table("user_profiles")


def downgrade() -> None:
    # Recreate user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=True),
        sa.Column("job_title", sa.String(256), nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("interests_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("goals_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("focus_areas_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("languages_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)

    # Drop new columns from users table using batch_alter_table for SQLite compatibility
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("preferences_json")
        batch_op.drop_column("personal_storage_path")
        batch_op.drop_column("vault_password_hash")
        batch_op.drop_column("handles_json")
        batch_op.drop_column("profile_photo")
        batch_op.drop_column("description")
        batch_op.drop_column("bio")
        batch_op.drop_column("nickname")
