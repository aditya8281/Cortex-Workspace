"""add privacy foundation models

Revision ID: a1b2c3d4e5f6
Revises: 954417ee7f03
Create Date: 2026-06-27 20:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "954417ee7f03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False, index=True),
        sa.Column("resource_id", sa.Integer(), nullable=True, index=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("session_id", sa.String(200), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("success", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )
    op.create_index("ix_audit_user_timestamp", "audit_logs", ["user_id", "timestamp"])
    op.create_index("ix_audit_resource_timestamp", "audit_logs", ["resource_type", "resource_id", "timestamp"])
    op.create_index("ix_audit_action_timestamp", "audit_logs", ["action", "timestamp"])

    # consent_records
    op.create_table(
        "consent_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("consent_type", sa.String(100), nullable=False),
        sa.Column("granted", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("scope", sa.String(200), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(500), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_consent_user_type", "consent_records", ["user_id", "consent_type"], unique=True)
    op.create_index("ix_consent_active", "consent_records", ["user_id", "granted", "expires_at"])

    # data_exports
    op.create_table(
        "data_exports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("export_type", sa.String(50), nullable=False, server_default="full"),
        sa.Column("data_types", sa.JSON(), nullable=True),
        sa.Column("format", sa.String(20), nullable=False, server_default="json"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # access_policies
    op.create_table(
        "access_policies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("effect", sa.String(10), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # privacy_roles
    op.create_table(
        "privacy_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # privacy_permissions
    op.create_table(
        "privacy_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # role_permissions (association)
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("privacy_roles.id"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("privacy_permissions.id"), primary_key=True),
    )

    # user_roles (association)
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
    )

    # data_deletion_requests
    op.create_table(
        "data_deletion_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("deletion_type", sa.String(50), nullable=False),
        sa.Column("data_types", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("items_deleted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deletion_proof_hash", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("data_deletion_requests")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("privacy_permissions")
    op.drop_table("privacy_roles")
    op.drop_table("access_policies")
    op.drop_table("data_exports")
    op.drop_table("consent_records")
    op.drop_table("audit_logs")
