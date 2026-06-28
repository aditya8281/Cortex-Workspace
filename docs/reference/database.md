Last updated: 2026-06-28

# CORTEX Database Reference

PostgreSQL 16 with SQLAlchemy 2.0 + Alembic migrations.

---

## Tables

| Table | Migration | Purpose |
|-------|-----------|---------|
| `users` | `a00000000001` | User accounts, credentials, profile |
| `auth_events` | `a00000000001` | Auth audit log (user_id, IP, timestamp, event_type) |
| `user_settings` | `x00000000023` | Per-user model settings |
| `user_model_settings` | `x00000000023` | Per-user model preferences |
| `knowledge_entries` | `t00000000019` | Knowledge base entries (text, vector, category, tags) |
| `storage_registries` | `e00000000005` | Per-user storage path pointers |
| `repo_indexes` | `j00000000010` | Repository metadata (FK to users), scan status |
| `code_chunks` | `j00000000010` | Indexed code with embeddings (FK to repo_indexes) |
| `graph_nodes` | `m00000000013` | Knowledge graph nodes (type, label, properties, embedding) |
| `graph_edges` | `m00000000013` | Knowledge graph edges (source, target, relation, weight) |
| `indexed_files` | `m00000000013` | File tracking for incremental indexing (path, hash, mtime) |
| `path_indices` | `y00000000024` | Path-based file lookup |
| `conversations` | `q00000000016` | Chat conversations (title, repo_id, model_used, token counts) |
| `messages` | `q00000000016` | Conversation messages (role, content, tokens) |
| `agents` | `n00000000014` | Agent definitions (name, description, config) |
| `agent_runs` | `n00000000014` | Agent execution history (status, task, result, metrics) |
| `agent_steps` | `n00000000014` | Individual steps within an agent run |
| `agent_feedback` | `n00000000014` | User feedback on agent runs (rating, comment) |
| `long_term_memory` | `i00000000009` | Persistent memories with decay, confidence, access tracking |
| `documents` | `a00000000001` | Non-code knowledge files (markdown, PDF, notebooks) |
| `document_chunks` | `a00000000001` | Chunked document content with embeddings |
| `model_catalog` | `r00000000017` | LLM model metadata (family, provider, capabilities) |
| `model_variants` | `r00000000017` | Quantization variants per model |
| `model_downloads` | `r00000000017` | Download tracking (status, progress, file path) |
| `model_usage` | `r00000000017` | Per-user model usage statistics |
| `providers` | `r00000000017` | LLM providers (Ollama, llama.cpp, etc.) |
| `provider_models` | `r00000000017` | Models available per provider |
| `capabilities` | `r00000000017` | Model capability tags (chat, code, vision) |
| `quantizations` | `r00000000017` | Quantization level definitions (Q4, Q8, FP16) |
| `hardware_profiles` | `r00000000017` | Detected hardware configurations |
| `sync_states` | `w00000000022` | File watcher sync state per repo per user |
| `indexing_configs` | `p00000000015` | Per-repo indexing rules (include/exclude paths, file types) |
| `embedding_cache` | `r00000000017` | Cached embeddings to avoid recomputation |
| `notifications` | `k00000000011` | System notifications for users |
| `episodic_memories` | `v10300000001` | Episodic memories (content, context, emotion, importance, confidence, recency, access_count) |
| `semantic_memories` | `v10300000002` | Semantic memories (content, category, confidence, source, access_count) |
| `working_memories` | `v10300000003` | Working memory (session_id, content, slot [active/buffer/archive], priority, expires_at) |
| `memory_nodes` | `v10300000004` | Memory graph nodes (memory_type, memory_id, label, embedding_id) — polymorphic link |
| `memory_edges` | `v10300000005` | Memory graph edges (source_id, target_id, edge_type, weight) — bidirectional |

---

## Migration Conventions

- **Naming**: Sequential prefix + descriptive name (`{letter}0000000000N_description.py`)
- **Both directions**: Every migration defines `upgrade()` and `downgrade()`
- **DDL**: Use `op.execute()` for raw SQL
- **Seed data**: Use `op.bulk_insert()` in migrations
- **Test**: Run `make db-reset` to verify migration chain
- **Create**: `make migration m="description"` after any model change
- **Apply**: `make migrate` (runs `alembic upgrade head`)

### Important

After any model change, run `make migration m="description"` then `make migrate`. Both `upgrade()` and `downgrade()` must be defined. Test with `make db-reset`.

---

## Schema Design Principles

1. **JSONB for flexible data**: `handles_json`, `preferences_json`, `tools_json`, `parameters_json` — avoids schema migration for semi-structured fields
2. **Soft deletes**: `deleted_at` column on user-facing tables
3. **Timestamps**: `created_at` and `updated_at` with `server_default=func.now()`
4. **Foreign keys with ON DELETE**: Explicit cascade rules (added in `f00000000006a`)
5. **Indexes**: Composite indexes for common query patterns (added in `d00000000004`)

---

## Session Management

- **ORM**: SQLAlchemy 2.0 with `Mapped[T]`, `mapped_column` syntax
- **Session**: Dynamic `SessionLocal` proxy; `get_engine()` creates engine lazily
- **Bootstrap**: `bootstrap_database()` runs `alembic upgrade head` on startup if DB URL points to local PostgreSQL
- **DI**: Always use `Depends(get_db)` in route handlers. Never create sessions manually.

---

## Gotchas

- Root `conftest.py` compiles `JSONB → JSON` for SQLite compatibility. Real DB uses JSONB.
- `migrations/env.py` imports all models for Alembic autogenerate to work.
- `start.sh` runs PostgreSQL on port 5435 (user-space). `docker-compose.yml` uses port 5432. These are different.
