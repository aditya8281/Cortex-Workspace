"""Add GIN indexes for full-text search.

Revision ID: u00000000020
Revises: t00000000019
Create Date: 2026-06-21
"""

from alembic import op

revision = "u00000000020"
down_revision = "t00000000019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX idx_code_chunks_content_fts ON code_chunks "
        "USING GIN (to_tsvector('english', content))"
    )
    op.execute(
        "CREATE INDEX idx_document_chunks_content_fts ON document_chunks "
        "USING GIN (to_tsvector('english', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_code_chunks_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_fts")
