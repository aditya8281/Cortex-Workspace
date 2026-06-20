"""knowledge_system_v2 — documents, document_chunks, embedding_cache

Revision ID: t00000000019
Revises: s00000000018
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

revision = "t00000000019"
down_revision = "s00000000018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    document_type_enum = PG_ENUM(
        "markdown", "pdf", "notebook", "text", "code", "other",
        name="document_type",
        create_type=False,
    )
    document_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("path", sa.String(2048), nullable=False, unique=True, index=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("doc_type", document_type_enum, nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(), nullable=True),
        sa.Column("embedding_model_version", sa.String(128), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_documents_type_deleted", "documents", ["doc_type", "deleted_at"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "document_id", sa.Integer(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_type", sa.String(32), nullable=False, server_default="paragraph"),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("context_before", sa.Text(), nullable=True),
        sa.Column("context_after", sa.Text(), nullable=True),
        sa.Column("embedding_id", sa.String(128), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_document_chunks_doc_index",
        "document_chunks",
        ["document_id", "chunk_index"],
        unique=True,
    )

    op.create_table(
        "embedding_cache",
        sa.Column("content_hash", sa.String(64), primary_key=True),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False, server_default="default"),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ttl_seconds", sa.Integer(), nullable=False, server_default="2592000"),
    )


def downgrade() -> None:
    op.drop_table("embedding_cache")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    PG_ENUM(name="document_type").drop(op.get_bind(), checkfirst=True)
