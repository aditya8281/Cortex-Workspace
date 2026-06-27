"""add awareness foundation models

Revision ID: 954417ee7f03
Revises: p06_add_v102_system_tables
Create Date: 2026-06-27 18:14:35.034982

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "954417ee7f03"
down_revision: str | Sequence[str] | None = "p06_add_v102_system_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create awareness foundation tables."""
    # --- device_info ---
    op.create_table(
        "device_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("os_type", sa.String(length=50), nullable=True),
        sa.Column("os_version", sa.String(length=100), nullable=True),
        sa.Column("cpu_cores", sa.Integer(), nullable=True),
        sa.Column("cpu_model", sa.String(length=255), nullable=True),
        sa.Column("total_memory_gb", sa.Integer(), nullable=True),
        sa.Column("available_memory_gb", sa.Integer(), nullable=True),
        sa.Column("disk_total_gb", sa.Integer(), nullable=True),
        sa.Column("disk_used_gb", sa.Integer(), nullable=True),
        sa.Column("python_version", sa.String(length=50), nullable=True),
        sa.Column(
            "last_checked",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_info_id", "device_info", ["id"], unique=False)
    op.create_index("ix_device_info_user_id", "device_info", ["user_id"], unique=False)
    op.create_index("ix_device_user", "device_info", ["user_id"], unique=True)

    # --- file_indices ---
    op.create_table(
        "file_indices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_extension", sa.String(length=50), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "indexed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("parent_directory", sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_file_content_hash", "file_indices", ["content_hash"], unique=False)
    op.create_index("ix_file_indices_content_hash", "file_indices", ["content_hash"], unique=False)
    op.create_index("ix_file_indices_file_extension", "file_indices", ["file_extension"], unique=False)
    op.create_index("ix_file_indices_id", "file_indices", ["id"], unique=False)
    op.create_index("ix_file_indices_user_id", "file_indices", ["user_id"], unique=False)
    op.create_index("ix_file_user_directory", "file_indices", ["user_id", "parent_directory"], unique=False)
    op.create_index("ix_file_user_extension", "file_indices", ["user_id", "file_extension"], unique=False)
    op.create_index("ix_file_user_path", "file_indices", ["user_id", "file_path"], unique=True)

    # --- project_indices ---
    op.create_table(
        "project_indices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_path", sa.String(length=1000), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("project_type", sa.String(length=100), nullable=True),
        sa.Column("frameworks", sa.String(length=500), nullable=True),
        sa.Column("configuration", sa.String(length=500), nullable=True),
        sa.Column(
            "last_scanned",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("has_tests", sa.Integer(), nullable=False),
        sa.Column("has_ci", sa.Integer(), nullable=False),
        sa.Column("has_docker", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_indices_id", "project_indices", ["id"], unique=False)
    op.create_index("ix_project_indices_user_id", "project_indices", ["user_id"], unique=False)
    op.create_index("ix_project_user_path", "project_indices", ["user_id", "project_path"], unique=True)
    op.create_index("ix_project_user_type", "project_indices", ["user_id", "project_type"], unique=False)

    # --- repository_indices ---
    op.create_table(
        "repository_indices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repo_path", sa.String(length=1000), nullable=False),
        sa.Column("repo_name", sa.String(length=255), nullable=False),
        sa.Column("languages", sa.String(length=500), nullable=True),
        sa.Column("total_files", sa.Integer(), nullable=False),
        sa.Column("total_lines", sa.Integer(), nullable=False),
        sa.Column(
            "last_indexed",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("framework", sa.String(length=100), nullable=True),
        sa.Column("dependencies", sa.String(length=500), nullable=True),
        sa.Column("git_branch", sa.String(length=200), nullable=True),
        sa.Column("last_commit_hash", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repo_user_framework", "repository_indices", ["user_id", "framework"], unique=False)
    op.create_index("ix_repo_user_path", "repository_indices", ["user_id", "repo_path"], unique=True)
    op.create_index("ix_repository_indices_id", "repository_indices", ["id"], unique=False)
    op.create_index("ix_repository_indices_user_id", "repository_indices", ["user_id"], unique=False)

    # --- system_health ---
    op.create_table(
        "system_health",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "last_check",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("check_details", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_service", "system_health", ["service_name"], unique=True)
    op.create_index("ix_health_status", "system_health", ["status"], unique=False)
    op.create_index("ix_system_health_id", "system_health", ["id"], unique=False)


def downgrade() -> None:
    """Drop awareness foundation tables."""
    op.drop_index("ix_system_health_id", table_name="system_health")
    op.drop_index("ix_health_status", table_name="system_health")
    op.drop_index("ix_health_service", table_name="system_health")
    op.drop_table("system_health")

    op.drop_index("ix_repository_indices_user_id", table_name="repository_indices")
    op.drop_index("ix_repository_indices_id", table_name="repository_indices")
    op.drop_index("ix_repo_user_path", table_name="repository_indices")
    op.drop_index("ix_repo_user_framework", table_name="repository_indices")
    op.drop_table("repository_indices")

    op.drop_index("ix_project_user_type", table_name="project_indices")
    op.drop_index("ix_project_user_path", table_name="project_indices")
    op.drop_index("ix_project_indices_user_id", table_name="project_indices")
    op.drop_index("ix_project_indices_id", table_name="project_indices")
    op.drop_table("project_indices")

    op.drop_index("ix_file_user_path", table_name="file_indices")
    op.drop_index("ix_file_user_extension", table_name="file_indices")
    op.drop_index("ix_file_user_directory", table_name="file_indices")
    op.drop_index("ix_file_indices_user_id", table_name="file_indices")
    op.drop_index("ix_file_indices_id", table_name="file_indices")
    op.drop_index("ix_file_indices_file_extension", table_name="file_indices")
    op.drop_index("ix_file_indices_content_hash", table_name="file_indices")
    op.drop_index("ix_file_content_hash", table_name="file_indices")
    op.drop_table("file_indices")

    op.drop_index("ix_device_user", table_name="device_info")
    op.drop_index("ix_device_info_user_id", table_name="device_info")
    op.drop_index("ix_device_info_id", table_name="device_info")
    op.drop_table("device_info")
