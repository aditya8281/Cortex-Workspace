"""Consolidated baseline migration — full schema from scratch.

Revision ID: b00000000000
Revises:
Create Date: 2026-06-22 00:00:00.000000

This migration replaces all 27 prior migrations (a00000000001 … z00000000025)
and creates the entire schema in one shot.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b00000000000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ENUM types ──────────────────────────────────────────────────────
    document_type = postgresql.ENUM(
        "markdown",
        "pdf",
        "notebook",
        "text",
        "code",
        "docx",
        "epub",
        "html",
        "pptx",
        "xlsx",
        "opendocument",
        "vcard",
        "ical",
        "archive",
        "image",
        "audio",
        "video",
        "font",
        "gis",
        "other",
        name="document_type",
        create_type=False,
    )
    document_type.create(op.get_bind(), checkfirst=True)

    # ── 1. users ────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), unique=True, nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("nickname", sa.String(), nullable=False, server_default=""),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("profile_photo", sa.String(), nullable=True),
        sa.Column("handles_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("vault_password_hash", sa.String(), nullable=True),
        sa.Column("vault_locked", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("preferences_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("github_username", sa.String(), unique=True, nullable=True),
        sa.Column("github_token_encrypted", sa.String(), nullable=True),
        sa.Column("programming_languages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("frameworks", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("current_projects", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("contribution_style", sa.String(32), nullable=True),
        sa.Column("social_links", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "users_role_check",
        "users",
        "role IN ('user', 'admin')",
    )

    # ── 2. auth_events ──────────────────────────────────────────────────
    op.create_table(
        "auth_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_auth_events_user_id", "auth_events", ["user_id"])

    # ── 3. knowledge_entries ────────────────────────────────────────────
    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_path", sa.String(1024), nullable=True),
        sa.Column("source_key", sa.String(512), nullable=True),
        sa.Column("embedding_id", sa.String(128), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("vector_collection", sa.String(64), nullable=False, server_default="cortex_memory"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_knowledge_entries_user_id", "knowledge_entries", ["user_id"])
    op.create_index("ix_knowledge_entries_category", "knowledge_entries", ["category"])
    op.create_index("ix_knowledge_entries_source_path", "knowledge_entries", ["source_path"])
    op.create_index("ix_knowledge_entries_source_key", "knowledge_entries", ["source_key"])
    op.create_index("ix_knowledge_entries_embedding_id", "knowledge_entries", ["embedding_id"])

    # ── 4. user_storage_registry ────────────────────────────────────────
    op.create_table(
        "user_storage_registry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("storage_root", sa.String(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_storage_registry_user_id", "user_storage_registry", ["user_id"])

    # ── 5. repo_indexes ─────────────────────────────────────────────────
    op.create_table(
        "repo_indexes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("repo_path", sa.String(2048), unique=True, nullable=False),
        sa.Column("repo_name", sa.String(256), nullable=False),
        sa.Column("primary_language", sa.String(64), nullable=True),
        sa.Column("total_files", sa.Integer(), server_default="0"),
        sa.Column("total_chunks", sa.Integer(), server_default="0"),
        sa.Column("last_commit", sa.String(64), nullable=True),
        sa.Column("last_indexed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_repo_indexes_user_id", "repo_indexes", ["user_id"])

    # ── 6. code_chunks ──────────────────────────────────────────────────
    op.create_table(
        "code_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(2048), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("symbol_type", sa.String(64), nullable=True),
        sa.Column("symbol_name", sa.String(256), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("embedding_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["repo_id"], ["repo_indexes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_code_chunks_repo_id", "code_chunks", ["repo_id"])
    op.create_index("ix_code_chunks_symbol_name", "code_chunks", ["symbol_name"])
    op.create_index("ix_code_chunks_embedding_id", "code_chunks", ["embedding_id"])

    # ── 7. notifications ────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False, server_default="system"),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── 8. graph_nodes ──────────────────────────────────────────────────
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("node_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("qualified_name", sa.String(1000), nullable=True),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("file_path", sa.String(2000), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["chunk_id"], ["code_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repo_id"], ["repo_indexes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_graph_nodes_chunk_id", "graph_nodes", ["chunk_id"])
    op.create_index("ix_graph_nodes_repo_id", "graph_nodes", ["repo_id"])
    op.create_index("ix_graph_nodes_node_type", "graph_nodes", ["node_type"])
    op.create_index("ix_graph_nodes_name", "graph_nodes", ["name"])
    op.create_index("ix_graph_nodes_file_path", "graph_nodes", ["file_path"])
    op.create_index("ix_graph_nodes_file_path_node_type", "graph_nodes", ["file_path", "node_type"])
    op.create_index("ix_graph_nodes_qualified_name", "graph_nodes", ["qualified_name"])

    # ── 9. graph_edges ──────────────────────────────────────────────────
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("edge_type", sa.String(50), nullable=False),
        sa.Column("weight", sa.Integer(), server_default="1"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("first_seen", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["graph_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["graph_nodes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_graph_edges_source_id", "graph_edges", ["source_id"])
    op.create_index("ix_graph_edges_target_id", "graph_edges", ["target_id"])
    op.create_index("ix_graph_edges_edge_type", "graph_edges", ["edge_type"])
    op.create_index("ix_graph_edges_source_id_edge_type", "graph_edges", ["source_id", "edge_type"])
    op.create_index("ix_graph_edges_target_id_edge_type", "graph_edges", ["target_id", "edge_type"])

    # ── 10. indexed_files ───────────────────────────────────────────────
    op.create_table(
        "indexed_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(2000), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size", sa.BigInteger(), server_default="0"),
        sa.Column("mtime", sa.Float(), server_default="0.0"),
        sa.Column("last_indexed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(20), server_default="indexed"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["repo_id"], ["repo_indexes.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_indexed_files_repo_id_file_path",
        "indexed_files",
        ["repo_id", "file_path"],
        unique=True,
    )

    # ── 11. agents ──────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("tools_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agents_user_id", "agents", ["user_id"])
    op.create_index("ix_agents_name", "agents", ["name"])

    # ── 12. agent_runs ──────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_runs_agent_id", "agent_runs", ["agent_id"])
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])

    # ── 13. agent_steps ─────────────────────────────────────────────────
    op.create_table(
        "agent_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("thought", sa.Text(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("action_input_json", sa.Text(), nullable=True),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_steps_run_id", "agent_steps", ["run_id"])
    op.create_index("ix_agent_steps_run_id_step_number", "agent_steps", ["run_id", "step_number"])

    # ── 14. agent_feedback ──────────────────────────────────────────────
    op.create_table(
        "agent_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_feedback_run_id", "agent_feedback", ["run_id"])
    op.create_index("ix_agent_feedback_user_id", "agent_feedback", ["user_id"])

    # ── 15. indexing_configs ────────────────────────────────────────────
    op.create_table(
        "indexing_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), server_default="default"),
        sa.Column("include_paths", sa.JSON(), nullable=True),
        sa.Column("exclude_paths", sa.JSON(), nullable=True),
        sa.Column("include_patterns", sa.JSON(), nullable=True),
        sa.Column("exclude_patterns", sa.JSON(), nullable=True),
        sa.Column("max_file_size_bytes", sa.Integer(), server_default="1000000"),
        sa.Column("follow_symlinks", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("sync_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("sync_interval_seconds", sa.Integer(), server_default="300"),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_indexing_configs_user_id", "indexing_configs", ["user_id"])

    # ── 16. conversations ───────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), server_default="New Conversation"),
        sa.Column("repo_id", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("message_count", sa.Integer(), server_default="0"),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repo_id"], ["repo_indexes.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_user_id_updated_at", "conversations", ["user_id", "updated_at"])

    # ── 17. conversation_messages ───────────────────────────────────────
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_conversation_messages_conversation_id",
        "conversation_messages",
        ["conversation_id"],
    )
    op.create_check_constraint(
        "conversation_messages_role_check",
        "conversation_messages",
        "role IN ('system', 'user', 'assistant')",
    )

    # ── 18. documents ───────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.String(2048), unique=True, nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "doc_type",
            postgresql.ENUM(
                "markdown",
                "pdf",
                "notebook",
                "text",
                "code",
                "docx",
                "epub",
                "html",
                "pptx",
                "xlsx",
                "opendocument",
                "vcard",
                "ical",
                "archive",
                "image",
                "audio",
                "video",
                "font",
                "gis",
                "other",
                name="document_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("last_indexed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("embedding_model_version", sa.String(128), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_documents_path", "documents", ["path"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])
    op.create_index("ix_documents_doc_type", "documents", ["doc_type"])
    op.create_index("ix_documents_deleted_at", "documents", ["deleted_at"])
    op.create_index("ix_documents_doc_type_deleted_at", "documents", ["doc_type", "deleted_at"])

    # ── 19. document_chunks ─────────────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_type", sa.String(32), nullable=False, server_default="paragraph"),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("context_before", sa.Text(), nullable=True),
        sa.Column("context_after", sa.Text(), nullable=True),
        sa.Column("embedding_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_embedding_id", "document_chunks", ["embedding_id"])
    op.create_index(
        "uq_document_chunks_document_id_chunk_index",
        "document_chunks",
        ["document_id", "chunk_index"],
        unique=True,
    )

    # ── 20. embedding_cache ─────────────────────────────────────────────
    op.create_table(
        "embedding_cache",
        sa.Column("content_hash", sa.String(64), primary_key=True),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False, server_default="default"),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_accessed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ttl_seconds", sa.Integer(), nullable=False, server_default="2592000"),
    )

    # ── 21. model_catalog ───────────────────────────────────────────────
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
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("recommended_use_cases", postgresql.JSONB(), nullable=True),
        sa.Column("not_recommended_for", postgresql.JSONB(), nullable=True),
        sa.Column("release_date", sa.String(20), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("family_version", sa.String(50), nullable=True),
        sa.Column("benchmarks", postgresql.JSONB(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("ollama_library_url", sa.Text(), nullable=True),
        sa.Column("huggingface_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("primary_provider_id", sa.Integer(), nullable=True),
        sa.Column("popularity_score", sa.Float(), server_default="0"),
        sa.Column("recency_score", sa.Float(), server_default="0"),
        sa.Column("efficiency_score", sa.Float(), server_default="0"),
        sa.Column("trending_score", sa.Float(), server_default="0"),
        sa.Column("total_downloads", sa.Integer(), server_default="0"),
        sa.Column("avg_rating", sa.Float(), nullable=True),
        sa.Column("rating_count", sa.Integer(), server_default="0"),
        sa.Column("last_updated", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_model_catalog_model_id", "model_catalog", ["model_id"])
    op.create_index("ix_model_catalog_family", "model_catalog", ["family"])

    # ── 22. model_variants ──────────────────────────────────────────────
    # SCHEMA DEBT: This table has overlapping columns with the quantizations table:
    #   - bits_per_param / quantization_bits overlap with quantizations.bits_per_param
    #   - quality_multiplier / speed_multiplier overlap with quantizations.quality_score/speed_multiplier
    # These should be consolidated in a future migration to reference quantizations directly.
    op.create_table(
        "model_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_catalog_id", sa.Integer(), nullable=False),
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
        sa.Column("compatible_backends", postgresql.JSONB(), nullable=True),
        sa.Column("downloaded", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("download_path", sa.Text(), nullable=True),
        sa.Column("ollama_tag", sa.String(255), nullable=True),
        sa.Column("huggingface_repo", sa.String(255), nullable=True),
        sa.Column("huggingface_file", sa.Text(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("provider_model_id", sa.Integer(), nullable=True),
        sa.Column("bits_per_param", sa.Float(), nullable=True),
        sa.Column("quality_multiplier", sa.Float(), nullable=True),
        sa.Column("speed_multiplier", sa.Float(), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("architecture", sa.String(100), nullable=True),
        sa.Column("quantization_bits", sa.Float(), nullable=True),
        sa.Column("last_downloaded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("download_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_catalog_id"], ["model_catalog.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_model_variants_model_catalog_id", "model_variants", ["model_catalog_id"])
    op.create_index("ix_model_variants_variant_id", "model_variants", ["variant_id"])
    op.create_index("ix_model_variants_downloaded", "model_variants", ["downloaded"])

    # ── 23. model_downloads ─────────────────────────────────────────────
    op.create_table(
        "model_downloads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_variant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Float(), server_default="0"),
        sa.Column("download_speed_bytes_sec", sa.Float(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_variant_id"], ["model_variants.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_model_downloads_user_id", "model_downloads", ["user_id"])
    op.create_index("ix_model_downloads_status", "model_downloads", ["status"])
    op.create_index("ix_model_downloads_user_id_status", "model_downloads", ["user_id", "status"])

    # ── 24. model_usage ─────────────────────────────────────────────────
    op.create_table(
        "model_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_variant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("usage_type", sa.String(50), nullable=True),
        sa.Column("tokens_prompt", sa.Integer(), nullable=True),
        sa.Column("tokens_completion", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("tps_generation", sa.Float(), nullable=True),
        sa.Column("tps_prompt", sa.Float(), nullable=True),
        sa.Column("context_length", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_variant_id"], ["model_variants.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_model_usage_model_variant_id", "model_usage", ["model_variant_id"])
    op.create_index("ix_model_usage_user_id", "model_usage", ["user_id"])

    # ── 25. providers ───────────────────────────────────────────────────
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("api_key_required", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("config_schema", postgresql.JSONB(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("health_status", sa.String(20), server_default="unknown"),
        sa.Column("last_health_check", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_providers_name", "providers", ["name"])
    op.create_index("ix_providers_provider_type", "providers", ["provider_type"])

    # ── 26. capabilities ────────────────────────────────────────────────
    op.create_table(
        "capabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_capabilities_name", "capabilities", ["name"])

    # ── 27. provider_models ─────────────────────────────────────────────
    op.create_table(
        "provider_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("provider_model_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("family", sa.String(100), nullable=True),
        sa.Column("parameter_count", sa.Float(), nullable=True),
        sa.Column("architecture", sa.String(100), nullable=True),
        sa.Column("context_length", sa.Integer(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(), nullable=True),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("download_url", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("quantization", sa.String(50), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("discovered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_provider_models_provider_id", "provider_models", ["provider_id"])
    op.create_index("ix_provider_models_family", "provider_models", ["family"])
    op.create_unique_constraint(
        "uq_provider_models_provider_id_provider_model_id",
        "provider_models",
        ["provider_id", "provider_model_id"],
    )

    # ── 28. quantizations ───────────────────────────────────────────────
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
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_quantizations_name", "quantizations", ["name"])

    # ── 29. hardware_profiles ───────────────────────────────────────────
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
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_user_defined", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_hardware_profiles_name", "hardware_profiles", ["name"])

    # ── 30. model_statistics ────────────────────────────────────────────
    op.create_table(
        "model_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_catalog_id", sa.Integer(), nullable=False),
        sa.Column("download_count_total", sa.Integer(), server_default="0"),
        sa.Column("download_count_period", sa.Integer(), server_default="0"),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("rating_count", sa.Integer(), server_default="0"),
        sa.Column("trending_score", sa.Float(), server_default="0"),
        sa.Column("last_downloaded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("average_tps", sa.Float(), nullable=True),
        sa.Column("average_vram_usage_gb", sa.Float(), nullable=True),
        sa.Column("benchmark_scores", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_catalog_id"], ["model_catalog.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_model_statistics_model_catalog_id", "model_statistics", ["model_catalog_id"]
    )
    op.create_index("ix_model_statistics_trending_score", "model_statistics", ["trending_score"])
    op.create_unique_constraint(
        "uq_model_statistics_model_catalog_id", "model_statistics", ["model_catalog_id"]
    )

    # ── 31. sync_jobs ───────────────────────────────────────────────────
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("sync_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("models_discovered", sa.Integer(), server_default="0"),
        sa.Column("models_updated", sa.Integer(), server_default="0"),
        sa.Column("models_added", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sync_jobs_provider_id", "sync_jobs", ["provider_id"])
    op.create_index("ix_sync_jobs_status", "sync_jobs", ["status"])

    # ── 32. long_term_memories ──────────────────────────────────────────
    op.create_table(
        "long_term_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("embedding_id", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decayed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_long_term_memories_user_id", "long_term_memories", ["user_id"])
    op.create_index(
        "ix_long_term_memories_user_id_category",
        "long_term_memories",
        ["user_id", "category"],
    )

    # ── 33. path_index ──────────────────────────────────────────────────
    op.create_table(
        "path_index",
        sa.Column("path", sa.String(2000), primary_key=True),
        sa.Column("parent_path", sa.String(2000), nullable=False),
        sa.Column("basename", sa.String(256), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("is_dir", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("file_count", sa.Integer(), server_default="0"),
        sa.Column("total_size", sa.BigInteger(), server_default="0"),
        sa.Column("last_modified", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repo_indexes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_path_index_parent_path", "path_index", ["parent_path"])
    op.create_index("ix_path_index_depth", "path_index", ["depth"])
    op.create_index("ix_path_index_repo_id", "path_index", ["repo_id"])
    op.create_index("ix_path_index_repo_id_parent_path", "path_index", ["repo_id", "parent_path"])
    op.create_index("ix_path_index_repo_id_depth", "path_index", ["repo_id", "depth"])

    # ── 34. sync_states ─────────────────────────────────────────────────
    op.create_table(
        "sync_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repo_path", sa.String(), nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("last_sync_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("files_watched", sa.Integer(), server_default="0"),
        sa.Column("files_changed", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["repo_id"], ["repo_indexes.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_sync_states_user_id", "sync_states", ["user_id"])
    op.create_index(
        "uq_sync_states_user_id_repo_path", "sync_states", ["user_id", "repo_path"], unique=True
    )

    # ── 35. user_model_settings ─────────────────────────────────────────
    op.create_table(
        "user_model_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), unique=True, nullable=False),
        sa.Column(
            "inference_backend", sa.String(50), nullable=False, server_default="auto"
        ),
        sa.Column("huggingface_token", sa.String(255), nullable=True),
        sa.Column("auto_download", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "max_concurrent_downloads", sa.Integer(), nullable=False, server_default="2"
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("uq_user_model_settings_user_id", "user_model_settings", ["user_id"], unique=True)

    # ── Back-fill model_catalog.provider FK (providers created first) ───
    op.create_foreign_key(
        "fk_model_catalog_primary_provider_id",
        "model_catalog",
        "providers",
        ["primary_provider_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_model_variants_provider_id",
        "model_variants",
        "providers",
        ["provider_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_model_variants_provider_model_id",
        "model_variants",
        "provider_models",
        ["provider_model_id"],
        ["id"],
    )

    # ── GIN full-text search indexes ────────────────────────────────────
    # NOTE: Alembic's op.create_index() does not support GIN indexes.
    # Raw DDL is required for PostgreSQL full-text search indexes.
    op.execute(
        "CREATE INDEX idx_code_chunks_content_fts "
        "ON code_chunks USING gin(to_tsvector('english', content))"
    )
    op.execute(
        "CREATE INDEX idx_document_chunks_content_fts "
        "ON document_chunks USING gin(to_tsvector('english', content))"
    )


def downgrade() -> None:
    # Drop in reverse dependency order.

    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_code_chunks_content_fts")

    op.drop_table("user_model_settings", if_exists=True)
    op.drop_table("sync_states", if_exists=True)
    op.drop_table("path_index", if_exists=True)
    op.drop_table("long_term_memories", if_exists=True)
    op.drop_table("model_usage", if_exists=True)
    op.drop_table("model_downloads", if_exists=True)
    op.drop_table("model_statistics", if_exists=True)
    op.drop_table("model_variants", if_exists=True)
    op.drop_table("model_catalog", if_exists=True)
    op.drop_table("sync_jobs", if_exists=True)
    op.drop_table("provider_models", if_exists=True)
    op.drop_table("hardware_profiles", if_exists=True)
    op.drop_table("quantizations", if_exists=True)
    op.drop_table("capabilities", if_exists=True)
    op.drop_table("providers", if_exists=True)
    op.drop_table("embedding_cache", if_exists=True)
    op.drop_table("document_chunks", if_exists=True)
    op.drop_table("documents", if_exists=True)
    op.drop_table("conversation_messages", if_exists=True)
    op.drop_table("conversations", if_exists=True)
    op.drop_table("indexing_configs", if_exists=True)
    op.drop_table("agent_feedback", if_exists=True)
    op.drop_table("agent_steps", if_exists=True)
    op.drop_table("agent_runs", if_exists=True)
    op.drop_table("agents", if_exists=True)
    op.drop_table("indexed_files", if_exists=True)
    op.drop_table("graph_edges", if_exists=True)
    op.drop_table("graph_nodes", if_exists=True)
    op.drop_table("notifications", if_exists=True)
    op.drop_table("code_chunks", if_exists=True)
    op.drop_table("repo_indexes", if_exists=True)
    op.drop_table("user_storage_registry", if_exists=True)
    op.drop_table("knowledge_entries", if_exists=True)
    op.drop_table("auth_events", if_exists=True)
    op.drop_table("users", if_exists=True)

    # Drop ENUM type last.
    postgresql.ENUM(name="document_type").drop(op.get_bind(), checkfirst=True)
