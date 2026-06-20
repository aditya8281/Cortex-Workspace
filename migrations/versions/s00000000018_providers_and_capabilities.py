"""providers and capabilities tables

Revision ID: s00000000018
Revises: r00000000017
Create Date: 2026-06-21 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "s00000000018"
down_revision: str | None = "r00000000017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Providers table
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("api_key_required", sa.Boolean(), server_default="false"),
        sa.Column("config_schema", postgresql.JSONB(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("health_status", sa.String(20), server_default="unknown"),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Capabilities table (model abilities)
    op.create_table(
        "capabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Provider models (raw model data from each provider before normalization)
    op.create_table(
        "provider_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_model_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("family", sa.String(100), nullable=True),
        sa.Column("parameter_count", sa.Float(), nullable=True),
        sa.Column("architecture", sa.String(100), nullable=True),
        sa.Column("context_length", sa.Integer(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("download_url", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("quantization", sa.String(50), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("provider_id", "provider_model_id", name="uq_provider_model"),
    )

    # Quantization definitions
    op.create_table(
        "quantizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("bits_per_param", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("speed_multiplier", sa.Float(), nullable=True),
        sa.Column("memory_multiplier", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Hardware profiles (for recommendation across different hardware)
    op.create_table(
        "hardware_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gpu_name", sa.String(200), nullable=True),
        sa.Column("gpu_type", sa.String(50), nullable=True),
        sa.Column("vram_gb", sa.Float(), nullable=True),
        sa.Column("ram_gb", sa.Float(), nullable=False),
        sa.Column("gpu_bandwidth_gbps", sa.Float(), nullable=True),
        sa.Column("compute_capability", sa.String(20), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default="false"),
        sa.Column("is_user_defined", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Model statistics (popularity, performance, trends)
    op.create_table(
        "model_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_catalog_id", sa.Integer(), sa.ForeignKey("model_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("download_count_total", sa.Integer(), server_default="0"),
        sa.Column("download_count_period", sa.Integer(), server_default="0"),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("rating_count", sa.Integer(), server_default="0"),
        sa.Column("trending_score", sa.Float(), server_default="0"),
        sa.Column("last_downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("average_tps", sa.Float(), nullable=True),
        sa.Column("average_vram_usage_gb", sa.Float(), nullable=True),
        sa.Column("benchmark_scores", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("model_catalog_id", name="uq_model_statistics"),
    )

    # Sync jobs tracking
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("sync_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("models_discovered", sa.Integer(), server_default="0"),
        sa.Column("models_updated", sa.Integer(), server_default="0"),
        sa.Column("models_added", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_providers_name", "providers", ["name"])
    op.create_index("ix_providers_type", "providers", ["provider_type"])
    op.create_index("ix_provider_models_provider", "provider_models", ["provider_id"])
    op.create_index("ix_provider_models_family", "provider_models", ["family"])
    op.create_index("ix_provider_models_discovered", "provider_models", ["discovered_at"])
    op.create_index("ix_quantizations_name", "quantizations", ["name"])
    op.create_index("ix_hardware_profiles_name", "hardware_profiles", ["name"])
    op.create_index("ix_model_statistics_catalog", "model_statistics", ["model_catalog_id"])
    op.create_index("ix_model_statistics_trending", "model_statistics", ["trending_score"])
    op.create_index("ix_sync_jobs_provider", "sync_jobs", ["provider_id"])
    op.create_index("ix_sync_jobs_status", "sync_jobs", ["status"])

    # Extend model_catalog
    op.add_column("model_catalog", sa.Column("primary_provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True))
    op.add_column("model_catalog", sa.Column("popularity_score", sa.Float(), server_default="0"))
    op.add_column("model_catalog", sa.Column("recency_score", sa.Float(), server_default="0"))
    op.add_column("model_catalog", sa.Column("efficiency_score", sa.Float(), server_default="0"))
    op.add_column("model_catalog", sa.Column("trending_score", sa.Float(), server_default="0"))
    op.add_column("model_catalog", sa.Column("total_downloads", sa.Integer(), server_default="0"))
    op.add_column("model_catalog", sa.Column("avg_rating", sa.Float(), nullable=True))
    op.add_column("model_catalog", sa.Column("rating_count", sa.Integer(), server_default="0"))

    # Extend model_variants
    op.add_column("model_variants", sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True))
    op.add_column("model_variants", sa.Column("provider_model_id", sa.Integer(), sa.ForeignKey("provider_models.id"), nullable=True))
    op.add_column("model_variants", sa.Column("bits_per_param", sa.Float(), nullable=True))
    op.add_column("model_variants", sa.Column("quality_multiplier", sa.Float(), nullable=True))
    op.add_column("model_variants", sa.Column("speed_multiplier", sa.Float(), nullable=True))
    op.add_column("model_variants", sa.Column("file_hash", sa.String(64), nullable=True))
    op.add_column("model_variants", sa.Column("file_url", sa.Text(), nullable=True))
    op.add_column("model_variants", sa.Column("architecture", sa.String(100), nullable=True))
    op.add_column("model_variants", sa.Column("quantization_bits", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("model_variants", "quantization_bits")
    op.drop_column("model_variants", "architecture")
    op.drop_column("model_variants", "file_url")
    op.drop_column("model_variants", "file_hash")
    op.drop_column("model_variants", "speed_multiplier")
    op.drop_column("model_variants", "quality_multiplier")
    op.drop_column("model_variants", "bits_per_param")
    op.drop_column("model_variants", "provider_model_id")
    op.drop_column("model_variants", "provider_id")

    op.drop_column("model_catalog", "rating_count")
    op.drop_column("model_catalog", "avg_rating")
    op.drop_column("model_catalog", "total_downloads")
    op.drop_column("model_catalog", "trending_score")
    op.drop_column("model_catalog", "efficiency_score")
    op.drop_column("model_catalog", "recency_score")
    op.drop_column("model_catalog", "popularity_score")
    op.drop_column("model_catalog", "primary_provider_id")

    op.drop_table("sync_jobs")
    op.drop_table("model_statistics")
    op.drop_table("hardware_profiles")
    op.drop_table("quantizations")
    op.drop_table("provider_models")
    op.drop_table("capabilities")
    op.drop_table("providers")
