"""Use 'simple' config for GIN full-text search indexes.

Revision ID: c00000000004
Revises: c00000000003
Create Date: 2026-06-22
"""

from alembic import op

revision = "c00000000004"
down_revision = "c00000000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Replace hardcoded 'english' config with 'simple' for language-agnostic indexing.
    op.execute("DROP INDEX IF EXISTS idx_code_chunks_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_fts")

    op.execute(
        "CREATE INDEX idx_code_chunks_content_fts "
        "ON code_chunks USING gin(to_tsvector('simple', content))"
    )
    op.execute(
        "CREATE INDEX idx_document_chunks_content_fts "
        "ON document_chunks USING gin(to_tsvector('simple', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_code_chunks_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_fts")

    op.execute(
        "CREATE INDEX idx_code_chunks_content_fts "
        "ON code_chunks USING gin(to_tsvector('english', content))"
    )
    op.execute(
        "CREATE INDEX idx_document_chunks_content_fts "
        "ON document_chunks USING gin(to_tsvector('english', content))"
    )
