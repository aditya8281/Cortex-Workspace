"""DB quality fixes — missing indexes and unique constraints.

Revision ID: c00000000003
Revises: c00000000002
Create Date: 2026-06-22 00:00:00.000000

Adds:
- Indexes on FK columns (model_variants.provider_id, provider_model_id, sync_states.repo_id)
- Unique constraint on code_chunks (repo_id, file_path, chunk_index)
- Unique constraint on knowledge_entries (user_id, source_path, category)
"""

from alembic import op
import sqlalchemy as sa

revision = "c00000000003"
down_revision = "c00000000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # FK column indexes for model_variants
    op.create_index("ix_model_variants_provider_id", "model_variants", ["provider_id"])
    op.create_index("ix_model_variants_provider_model_id", "model_variants", ["provider_model_id"])

    # FK column index for sync_states
    op.create_index("ix_sync_states_repo_id", "sync_states", ["repo_id"])

    # Unique constraint for code_chunks (repo_id, file_path, chunk_index)
    op.create_unique_constraint(
        "uq_code_chunks_repo_file_index",
        "code_chunks",
        ["repo_id", "file_path", "chunk_index"],
    )

    # Unique constraint for knowledge_entries (user_id, source_path, category)
    op.create_unique_constraint(
        "uq_knowledge_entries_user_source_category",
        "knowledge_entries",
        ["user_id", "source_path", "category"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_knowledge_entries_user_source_category", "knowledge_entries", type_="unique")
    op.drop_constraint("uq_code_chunks_repo_file_index", "code_chunks", type_="unique")
    op.drop_index("ix_sync_states_repo_id", table_name="sync_states")
    op.drop_index("ix_model_variants_provider_model_id", table_name="model_variants")
    op.drop_index("ix_model_variants_provider_id", table_name="model_variants")
