"""model_catalog tables

Revision ID: r00000000017
Revises: q00000000016
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "r00000000017"
down_revision: str | None = "q00000000016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_id", sa.String(255), unique=True, nullable=False),
        sa.Column("family", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("parameter_count", sa.Float(), nullable=True),
        sa.Column("architecture", sa.String(100), nullable=True),
        sa.Column("context_length_default", sa.Integer(), nullable=True),
        sa.Column("context_length_max", sa.Integer(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("recommended_use_cases", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("not_recommended_for", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("release_date", sa.String(20), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("family_version", sa.String(50), nullable=True),
        sa.Column("benchmarks", postgresql.JSONB(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("ollama_library_url", sa.Text(), nullable=True),
        sa.Column("huggingface_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "model_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "model_catalog_id", sa.Integer(), sa.ForeignKey("model_catalog.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("variant_id", sa.String(255), unique=True, nullable=False),
        sa.Column("quantization", sa.String(50), nullable=False),
        sa.Column("quantization_level", sa.String(20), nullable=True),
        sa.Column("parameter_count", sa.Float(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("size_gb", sa.Float(), nullable=True),
        sa.Column("vram_required_gb", sa.Float(), nullable=True),
        sa.Column("ram_required_gb", sa.Float(), nullable=True),
        sa.Column("recommended_vram_gb", sa.Float(), nullable=True),
        sa.Column("estimated_tps_gpu", sa.Float(), nullable=True),
        sa.Column("estimated_tps_cpu", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("compatible_backends", postgresql.JSONB(), nullable=True, server_default='["ollama", "llama_cpp"]'),
        sa.Column("downloaded", sa.Boolean(), server_default="false"),
        sa.Column("download_path", sa.Text(), nullable=True),
        sa.Column("ollama_tag", sa.String(255), nullable=True),
        sa.Column("huggingface_repo", sa.String(255), nullable=True),
        sa.Column("huggingface_file", sa.Text(), nullable=True),
        sa.Column("last_downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("download_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "model_downloads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_variant_id", sa.Integer(), sa.ForeignKey("model_variants.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Float(), server_default="0"),
        sa.Column("download_speed_bytes_sec", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "model_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_variant_id", sa.Integer(), sa.ForeignKey("model_variants.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("usage_type", sa.String(50), nullable=True),
        sa.Column("tokens_prompt", sa.Integer(), nullable=True),
        sa.Column("tokens_completion", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("tps_generation", sa.Float(), nullable=True),
        sa.Column("tps_prompt", sa.Float(), nullable=True),
        sa.Column("context_length", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_model_catalog_family", "model_catalog", ["family"])
    op.create_index("ix_model_catalog_model_id", "model_catalog", ["model_id"])
    op.create_index("ix_model_variants_catalog_id", "model_variants", ["model_catalog_id"])
    op.create_index("ix_model_variants_downloaded", "model_variants", ["downloaded"])
    op.create_index("ix_model_downloads_status", "model_downloads", ["status"])
    op.create_index("ix_model_downloads_user", "model_downloads", ["user_id"])
    op.create_index("ix_model_usage_variant", "model_usage", ["model_variant_id"])
    op.create_index("ix_model_usage_user", "model_usage", ["user_id"])


def downgrade() -> None:
    op.drop_table("model_usage")
    op.drop_table("model_downloads")
    op.drop_table("model_variants")
    op.drop_table("model_catalog")
