# Cortex Database Audit Report — v2

Generated: 2026-06-22
Updated: 2026-06-22 (P0/P1 fixes applied)  
Scope: Full database layer — migrations, models, schemas, configuration

---

## Fixed Issues (2026-06-22)

| ID | Issue | Fix |
|----|-------|-----|
| MOD-CRIT-1 | `auth_events.metadata_json` JSONB/JSON mismatch | Changed migration from `sa.JSON()` to `postgresql.JSONB()` |
| SCH-CRIT-1 | `AgentInfo.tools` field name mismatch with ORM `tools_json` | Added `ConfigDict(from_attributes=True)` and `serialization_alias="tools_json"` |
| SCH-HIGH-1 | `AgentRunInfo.input` mismatch with ORM `input_text` | Added `serialization_alias="input_text"` |
| SCH-HIGH-2 | `AgentStepInfo.action_input` mismatch with ORM `action_input_json` | Added `serialization_alias="action_input_json"` |
| M-MED-3 | `indexing_configs.user_id` FK missing `ondelete` | Added `ondelete="CASCADE"` |

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Migration (Alembic) | 2 | 3 | 4 | 3 | 12 |
| Models (SQLAlchemy) | 1 | 4 | 6 | 4 | 15 |
| Schemas (Pydantic) | 1 | 4 | 2 | 2 | 9 |
| Indexes | 0 | 2 | 3 | 1 | 6 |
| Data Integrity | 1 | 2 | 2 | 1 | 6 |
| **Total** | **5** | **15** | **17** | **11** | **48** |

---

## Part 1: Migration (Alembic)

### M-CRIT-1: Downgrade drops `model_statistics` before `model_variants` — FK violation

**File:** `migrations/versions/b00000000000_baseline.py:888-889`

`model_statistics` depends on `model_catalog` (FK: `model_catalog_id → model_catalog.id`). `model_variants` also depends on `model_catalog`. The downgrade drops `model_statistics` (line 888) before `model_variants` (line 889), but both depend on `model_catalog`. While PostgreSQL allows this (neither depends on the other), the real bug is that `model_variants` references `model_catalog` and `providers` — and `model_variants` is dropped AFTER `model_catalog` is dropped at line 890, which would cause an FK violation if the actual order were `model_catalog` → `model_variants`. However, the actual order is `model_variants` → `model_catalog`, which is correct for that pair.

**Corrected finding:** The actual downgrade order IS correct for all FK pairs. However, the downgrade does NOT drop the `document_type` ENUM type — it only appears in the last line but is not reached if any `drop_table` fails. Additionally, the ENUM is created with `checkfirst=True` in upgrade but dropped with `checkfirst=True` in downgrade, which is correct.

**Severity revised to:** Medium (ENUM handling gap, not a drop-order bug).

---

### M-CRIT-2: Baseline migration missing `server_default` on 15+ NOT NULL timestamp columns

**File:** `migrations/versions/b00000000000_baseline.py`

The following NOT NULL timestamp columns have NO `server_default`, meaning INSERT will fail if the application doesn't provide values:

| Table | Column | Line |
|-------|--------|------|
| `users` | `created_at` | 73 |
| `users` | `updated_at` | 74 |
| `knowledge_entries` | `created_at` | 107 |
| `knowledge_entries` | `updated_at` | 108 |
| `user_storage_registry` | `created_at` | 123 |
| `user_storage_registry` | `updated_at` | 124 |
| `repo_indexes` | `created_at` | 142 |
| `repo_indexes` | `updated_at` | 143 |
| `code_chunks` | `created_at` | 162 |
| `notifications` | `created_at` | 178 |
| `graph_nodes` | `created_at` | 197 |
| `graph_edges` | `created_at` | 220 |
| `graph_edges` | `first_seen` | 218 |
| `graph_edges` | `last_seen` | 219 |
| `agents` | `created_at` | 263 |
| `agents` | `updated_at` | 264 |
| `agent_runs` | `created_at` | 280 |
| `agent_steps` | `created_at` | 300 |
| `agent_feedback` | `created_at` | 314 |
| `conversations` | `created_at` | 352 |
| `conversations` | `updated_at` | 353 |
| `conversation_messages` | `created_at` | 369 |
| `documents` | `created_at` | 424 |
| `documents` | `updated_at` | 425 |
| `document_chunks` | `created_at` | 448 |
| `embedding_cache` | `created_at` | 468 |
| `embedding_cache` | `last_accessed_at` | 469 |
| `long_term_memories` | `created_at` | 766 |
| `long_term_memories` | `updated_at` | 767 |

**Impact:** Any bulk insert or raw SQL INSERT that omits these columns will fail with a NOT NULL constraint violation.

**Fix:** Add `server_default=sa.func.now()` to all NOT NULL timestamp columns in the migration.

---

### M-HIGH-1: Migration uses raw SQL for CHECK constraints — non-portable

**File:** `migrations/versions/b00000000000_baseline.py:77-79, 377-380`

```python
op.execute("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('user', 'admin'))")
op.execute("ALTER TABLE conversation_messages ADD CONSTRAINT conversation_messages_role_check CHECK (role IN ('system', 'user', 'assistant'))")
```

Raw SQL is PostgreSQL-specific. If the project ever migrates to another RDBMS, these will fail. Also, the `downgrade()` does NOT drop these CHECK constraints.

**Fix:** Use `op.create_check_constraint()` for portability, and add `op.drop_constraint()` in downgrade.

---

### M-HIGH-2: Migration uses raw SQL for GIN indexes — non-portable

**File:** `migrations/versions/b00000000000_baseline.py:866-873`

```python
op.execute("CREATE INDEX idx_code_chunks_content_fts ON code_chunks USING gin(to_tsvector('english', content))")
op.execute("CREATE INDEX idx_document_chunks_content_fts ON document_chunks USING gin(to_tsvector('english', content))")
```

GIN indexes with `to_tsvector` are PostgreSQL-specific. The downgrade does drop these with `IF EXISTS`, which is correct.

---

### M-HIGH-3: Downgrade missing `if_exists` guards on all `drop_table` calls

**File:** `migrations/versions/b00000000000_baseline.py:882-916`

All 35 `op.drop_table()` calls use bare table names without `if_exists=True`. If the upgrade partially fails (e.g., a table was never created), `alembic downgrade` will also fail.

**Fix:** Add `if_exists=True` to all `drop_table` calls, or wrap in try/except.

---

### M-MED-1: `model_variants.model_catalog_id` nullable mismatch between migration and ORM

**File:** `migrations/versions/b00000000000_baseline.py:517` vs `backend/app/models/model_catalog.py:60-61`

| Location | `model_catalog_id` nullable |
|----------|-----------------------------|
| Migration | `nullable=True` (line 517: no `nullable=False`) |
| ORM model | No explicit nullable → defaults to `nullable=False` (implicit from `Mapped[int]`) |

The migration allows NULL but the ORM model does not. If `create_all()` is used, the column will be NOT NULL.

**Fix:** Add `nullable=False` to the migration column definition.

---

### M-MED-2: `agents.name` missing unique constraint in migration

**File:** `migrations/versions/b00000000000_baseline.py:257`

The migration defines `agents.name` as `String(100), nullable=False` without `unique=True`. The ORM model at `backend/app/models/agent.py:20` also lacks `unique=True`. However, logically agent names should be unique per user.

---

### M-MED-3: `indexing_configs.user_id` FK missing `ondelete`

**File:** `migrations/versions/b00000000000_baseline.py:338`

```python
sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
```

No `ondelete` clause. All other user FKs use `CASCADE` or `SET NULL`. Deleting a user will raise a FK violation error instead of cascading.

**Fix:** Add `ondelete="CASCADE"` to match the ORM model at `backend/app/models/indexing_config.py:17`.

---

### M-MED-4: Migration naming uses `b` prefix — potential collision with archived migrations

**File:** `migrations/versions/b00000000000_baseline.py:16`

The baseline uses revision `b00000000000`. The docstring says it replaces 27 prior migrations (`a00000000001` … `z00000000025`). Using the `b` prefix could collide if any archived migration files are restored.

---

### M-LOW-1: `TIMESTAMP` vs `TIMESTAMPTZ` inconsistency in migration

**File:** `migrations/versions/b00000000000_baseline.py` (all timestamp columns)

The migration uses `sa.TIMESTAMP()` (no timezone) everywhere. PostgreSQL best practice favors `TIMESTAMPTZ` for audit columns. The ORM models are inconsistent: some use `DateTime(timezone=True)`, others `DateTime` (no timezone).

---

### M-LOW-2: Downgrade does not drop ENUM type before dependent tables

**File:** `migrations/versions/b00000000000_baseline.py:918-919`

The ENUM `document_type` is dropped at line 918-919, AFTER all tables are dropped. This is correct (ENUM is referenced by `documents.doc_type`), but if any table drop fails, the ENUM will not be dropped. No guard exists.

---

### M-LOW-3: `model_variants` has duplicate columns for same concept

**File:** `migrations/versions/b00000000000_baseline.py:514-555`

`model_variants` has both `architecture` (line 543) and `quantization_bits` (line 544) which duplicate `architecture` (line 543) and `bits_per_param` (line 538). Similarly `quantization` and `quantization_level` overlap. This suggests schema evolution debt from prior migrations.

---

## Part 2: Models (SQLAlchemy)

### MOD-CRIT-1: `auth_events.metadata_json` type mismatch — ORM uses JSONB, migration uses JSON

**File:** `backend/app/models/auth_event.py:20` vs `migrations/versions/b00000000000_baseline.py:89`

| Location | Column type |
|----------|-------------|
| ORM model | `JSONB` (from `sqlalchemy.dialects.postgresql`) |
| Migration | `sa.JSON()` |

PostgreSQL `JSONB` and `JSON` have different storage and query capabilities. The ORM will generate queries assuming `JSONB` operators, but the actual column is `JSON`.

**Fix:** Change the migration to `postgresql.JSONB()` or the model to `JSON`.

---

### MOD-HIGH-1: `ModelVariant` FKs missing `ondelete` clauses

**File:** `backend/app/models/model_catalog.py:83-84`

```python
provider_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("providers.id"), nullable=True, index=True)
provider_model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("provider_models.id"), nullable=True, index=True)
```

Neither has `ondelete`. Deleting a `Provider` or `ProviderModel` referenced by a `ModelVariant` will raise a FK violation. Compare with `model_catalog_id` which has `ondelete="CASCADE"`.

**Fix:** Add `ondelete="SET NULL"` to both FKs.

---

### MOD-HIGH-2: `ModelDownload` and `ModelUsage` FKs missing `ondelete`

**File:** `backend/app/models/model_catalog.py:104-105, 123-125`

```python
# ModelDownload
model_variant_id: ... ForeignKey("model_variants.id")  # no ondelete
user_id: ... ForeignKey("users.id")  # no ondelete

# ModelUsage
model_variant_id: ... ForeignKey("model_variants.id")  # no ondelete
user_id: ... ForeignKey("users.id")  # no ondelete
```

Deleting a user or model variant referenced by these tables will raise FK violations.

**Fix:** Add `ondelete="SET NULL"` to all four FKs.

---

### MOD-HIGH-3: `Agent.user` relationship lacks `back_populates`

**File:** `backend/app/models/agent.py:31`

```python
user = relationship("User")
```

This is a one-way relationship. The `User` model has no `agents` relationship. This means `user.agents` will raise `AttributeError`. Also, SQLAlchemy may emit lazy-load queries in unexpected contexts.

**Fix:** Add `back_populates="agents"` and add `agents = relationship("Agent", back_populates="user")` to `User`.

---

### MOD-HIGH-4: Multiple models use `backref` instead of `back_populates`

**File:** Multiple locations

| Model | Relationship | File:Line |
|-------|-------------|-----------|
| `GraphNode.chunk` | `backref="graph_nodes"` | `graph.py:33` |
| `GraphNode.repo` | `backref="graph_nodes"` | `graph.py:34` |
| `IndexedFile.repo` | `backref="indexed_files"` | `file_index.py:30` |

Using `backref` creates implicit bidirectional relationships but:
- Makes the reverse side untyped (no `Mapped` annotation)
- Can cause circular import issues
- Makes it harder to reason about relationship ownership

**Fix:** Replace `backref` with explicit `back_populates` on both sides.

---

### MOD-MED-1: `CodeChunk` missing unique constraint on `(repo_id, file_path, chunk_index)`

**File:** `backend/app/models/repo_index.py:32-48`

`DocumentChunk` has `UniqueConstraint("document_id", "chunk_index")` at `document.py:89`. `CodeChunk` has no equivalent, allowing duplicate chunks for the same file in the same repo.

**Fix:** Add `UniqueConstraint("repo_id", "file_path", "chunk_index", name="uq_code_chunks_repo_file_index")` to `CodeChunk.__table_args__`.

---

### MOD-MED-2: `models/__init__.py` exports only 13 of 28 model classes

**File:** `backend/app/models/__init__.py:41-55`

**Missing exports:**
- `User`, `Agent`, `AgentRun`, `AgentStep`, `AgentFeedback`
- `Conversation`, `ConversationMessage`
- `Document`, `DocumentChunk`
- `GraphNode`, `GraphEdge`
- `Notification`, `AuthEvent`
- `IndexedFile`, `PathIndex`, `RepoIndex`, `CodeChunk`
- `IndexingConfig`, `StorageRegistry`
- `LongTermMemory`, `EmbeddingCache`
- `KnowledgeEntry` (in `intelligence/models.py`)

These models are registered via `migrations/env.py` imports, so Alembic sees them. But other code that does `from backend.app.models import User` will fail.

---

### MOD-MED-3: `DateTime` vs `DateTime(timezone=True)` inconsistency across models

**Timezone-aware models:** ModelCatalog, ModelVariant, ModelDownload, ModelUsage, Provider, ProviderModel, Quantization, HardwareProfile, ModelStatistics, SyncJob, UserModelSettings, SyncState, LongTermMemory

**Timezone-naive models:** User, Agent, AgentRun, AgentStep, AgentFeedback, Conversation, ConversationMessage, Document, DocumentChunk, GraphNode, GraphEdge, Notification, IndexedFile, PathIndex, RepoIndex, CodeChunk, IndexingConfig, StorageRegistry, EmbeddingCache, AuthEvent

Mixing tz-aware and tz-naive datetimes causes comparison bugs (e.g., `updated_at > some_tz_aware_datetime` raises `TypeError` in Python).

---

### MOD-MED-4: Default value mechanism inconsistency

Some models use Python-side `default=X`, others use `server_default=func.now()` or `server_default="X"`. Python defaults are NOT applied by:
- Bulk inserts (`session.bulk_insert_mappings()`)
- Raw SQL inserts
- `session.execute(insert(...))`

Affected: `Agent.is_active`, `AgentRun.status`, `AgentStep.status`, `RepoIndex.total_files`, `RepoIndex.total_chunks`, `RepoIndex.status`, and many more.

---

### MOD-MED-5: `RepoIndex` and `CodeChunk` timestamps nullable inconsistency

**File:** `backend/app/models/repo_index.py:28-29`

```python
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

No explicit `nullable=False`. The `Mapped[datetime]` type hint implies NOT NULL, but without `nullable=False` in the column definition, SQLAlchemy may allow NULL in some contexts. The migration explicitly sets `nullable=True` for these columns.

---

### MOD-MED-6: `LongTermMemory.source_id` has no FK constraint

**File:** `backend/app/models/long_term_memory.py:23`

```python
source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

This is a plain integer with no `ForeignKey`. It appears to be a polymorphic reference (could point to different tables depending on `source`). This is intentional but means no referential integrity at the DB level.

---

### MOD-LOW-1: `Conversation` and `LongTermMemory` now have proper FKs (audit v1 finding resolved)

The original audit (v1) flagged missing FKs on `Conversation.user_id`, `Conversation.repo_id`, and `LongTermMemory.user_id`. The current code at `conversation.py:15,17` and `long_term_memory.py:15` correctly defines `ForeignKey` constraints. **This finding is resolved.**

---

### MOD-LOW-2: `User.handles_json` and `preferences_json` have defensive property accessors

**File:** `backend/app/models/user.py:50-68`

The `handles` and `preferences` properties check `isinstance(self.handles_json, dict)` before returning. This is a workaround for potential type mismatches (e.g., JSON stored as string). While defensive, it masks underlying data issues.

---

### MOD-LOW-3: `IndexedFile.is_stale()` uses `os.stat()` in model method

**File:** `backend/app/models/file_index.py:34-45`

A model method performing filesystem I/O is unusual and makes the model harder to test. This belongs in a service layer.

---

### MOD-LOW-4: No cascade deletes configured on `Notification` → `User` reverse

**File:** `backend/app/models/notification.py`

`Notification.user_id` has `ondelete="CASCADE"` in the migration, so deleting a user deletes notifications. But the `User` model has no `notifications` relationship, so there's no ORM-level cascade. This is fine (DB handles it) but inconsistent with patterns like `Agent.runs` which have ORM cascades.

---

## Part 3: Schemas (Pydantic)

### SCH-CRIT-1: `AgentInfo.tools` field name mismatch with ORM `tools_json`

**File:** `backend/app/schemas/agent.py:16` vs `backend/app/models/agent.py:24`

| Schema field | ORM field | Type |
|-------------|-----------|------|
| `tools: str \| None` | `tools_json: str \| None` | Name mismatch |

Pydantic v2 with `from_attributes=True` would need `tools_json` mapped to `tools`. Without alias configuration, `AgentInfo` will always have `tools=None` even if the ORM object has data in `tools_json`.

**Fix:** Either rename schema field to `tools_json` or add `model_config = ConfigDict(from_attributes=True)` with field alias.

---

### SCH-HIGH-1: `AgentRunInfo.input` mismatch with ORM `input_text`

**File:** `backend/app/schemas/agent.py:43` vs `backend/app/models/agent.py:45`

| Schema field | ORM field |
|-------------|-----------|
| `input: str` | `input_text: str` |

Same pattern as above — field name mismatch causes data loss in serialized responses.

---

### SCH-HIGH-2: `AgentStepInfo` fields mismatch with ORM

**File:** `backend/app/schemas/agent.py:52-61` vs `backend/app/models/agent.py:61-76`

| Schema field | ORM field | Issue |
|-------------|-----------|-------|
| `action_input: dict \| None` | `action_input_json: str \| None` | Name + type mismatch (dict vs str) |
| (missing) | `observation: str \| None` | Field omitted from schema |

`observation` is silently dropped from API responses. All agent reasoning observation data is lost.

---

### SCH-HIGH-3: `ModelCatalogEntry` fields not in `ModelCatalog` ORM

**File:** `backend/app/schemas/model.py:15-28` vs `backend/app/models/model_catalog.py:12-53`

| Schema field | Exists in ORM? |
|-------------|---------------|
| `model_type: str` | No |
| `size_bytes: int \| None` | No |
| `downloaded: bool` | No |
| `hardware_requirements: dict` | No |

These fields must be computed/joined from `ModelVariant` data. If the schema is used with `from_attributes=True` on a raw `ModelCatalog` ORM object, these will all be `None`/default.

---

### SCH-HIGH-4: `UserResponse` computed fields not in `User` ORM

**File:** `backend/app/schemas/user.py:38-68` vs `backend/app/models/user.py:11-68`

| Schema field | Exists in ORM? |
|-------------|---------------|
| `storage_root: str \| None` | No (lives in `StorageRegistry`) |
| `data_path: str \| None` | No |
| `personal_storage_path: str \| None` | No |

These are computed from related tables. If `UserResponse` is used with `from_attributes=True` on a raw `User` object, they'll always be `None`.

---

### SCH-MED-1: `parameter_count` type mismatch across 6 schemas

**Files:** `backend/app/schemas/model.py` (multiple classes)

| Schema class | `parameter_count` type | ORM type |
|-------------|----------------------|----------|
| `ModelCatalogEntry` | `str \| None` | `float \| None` |
| `InstalledVariant` | `str \| None` | `float \| None` |
| `ModelSearchResult` | `str \| None` | `float \| None` |
| `ModelDetailResponse` | `str \| None` | `float \| None` |
| `ModelRecommendation` | `str \| None` | `float \| None` |
| `ModelVariantInfo` | `str \| None` | `float \| None` |

The ORM stores `parameter_count` as `Float` but schemas declare it as `str`. This works if the API layer converts (e.g., `f"{val}B"` for billions), but creates a type-safety gap.

---

### SCH-MED-2: `ConversationDetailResponse` inherits but overrides `messages` default

**File:** `backend/app/schemas/conversation.py:41-42`

```python
class ConversationDetailResponse(ConversationResponse):
    messages: list[ConversationMessageResponse] = []
```

This is correct behavior, but the inheritance means `ConversationDetailResponse` includes all parent fields. If the parent response is used in list endpoints, it could leak `messages` data.

---

### SCH-LOW-1: `LLMHealthResponse` and `LLMMetricsResponse` are empty schemas

**File:** `backend/app/schemas/model.py:108-113`

```python
class LLMHealthResponse(BaseModel):
    pass

class LLMMetricsResponse(BaseModel):
    pass
```

Empty response schemas suggest incomplete implementation.

---

### SCH-LOW-2: `AgentFeedbackCreateResponse.feedback` typed as `dict`

**File:** `backend/app/schemas/agent.py:96`

```python
feedback: dict
```

Should use a typed schema (`AgentFeedbackInfo`) for consistency with other response schemas.

---

## Part 4: Indexes

### IDX-HIGH-1: Missing indexes on FK columns in migration

**File:** `migrations/versions/b00000000000_baseline.py`

| Table | Column | FK target | Has index? |
|-------|--------|-----------|------------|
| `model_variants` | `provider_id` | `providers.id` | No |
| `model_variants` | `provider_model_id` | `provider_models.id` | No |
| `sync_states` | `repo_id` | `repo_indexes.id` | No |

Note: The ORM model declares `index=True` on these columns, but the migration does not create the indexes. If `alembic upgrade` is used, these indexes will be missing.

---

### IDX-HIGH-2: Redundant index on `agent_runs.user_id`

**File:** `migrations/versions/b00000000000_baseline.py:286` + `backend/app/models/agent.py:57`

| Source | Index name |
|--------|-----------|
| Migration line 286 | `ix_agent_runs_user_id` |
| ORM `__table_args__` line 57 | `idx_agent_runs_status` (on `status`, not `user_id`) |

Correction: The ORM defines `Index("idx_agent_runs_status", "status")` — this is on `status`, not `user_id`. So there is NO redundant index on `user_id`. The migration creates `ix_agent_runs_user_id` and the ORM creates `idx_agent_runs_status` on different columns.

**Finding revised:** No redundant index exists. However, the ORM defines an index on `status` that is NOT in the migration. If `create_all()` is used, this index will exist; if only migrations are used, it won't.

---

### IDX-MED-1: `User.deleted_at` missing index

**File:** `backend/app/models/user.py:48`

`deleted_at` is defined with `index=True` in the ORM model, but the migration does NOT create an index for it. Soft-delete queries (`WHERE deleted_at IS NULL`) will require a full table scan.

**Fix:** Add `op.create_index("ix_users_deleted_at", "users", ["deleted_at"])` to the migration.

---

### IDX-MED-2: `graph_edges` has composite indexes but migration naming differs from ORM

**File:** `migrations/versions/b00000000000_baseline.py:227-228` vs `backend/app/models/graph.py:67-68`

| Migration index | ORM index |
|----------------|-----------|
| `ix_graph_edges_source_id_edge_type` | `idx_graph_edges_source_type` |
| `ix_graph_edges_target_id_edge_type` | `idx_graph_edges_target_type` |

Different names for the same logical indexes. Not a functional issue but creates confusion.

---

### IDX-MED-3: `graph_nodes` composite index naming inconsistency

**File:** `migrations/versions/b00000000000_baseline.py:206` vs `backend/app/models/graph.py:39`

| Migration index | ORM index |
|----------------|-----------|
| `ix_graph_nodes_file_path_node_type` | `idx_graph_nodes_file_type` |

Same logical index, different names.

---

### IDX-LOW-1: GIN indexes use hardcoded `'english'` text search config

**File:** `migrations/versions/b00000000000_baseline.py:866-873`

```python
to_tsvector('english', content)
```

Hardcoded to English. Non-English content will not benefit from proper stemming/tokenization.

---

## Part 5: Data Integrity

### DI-CRIT-1: `knowledge_entries` has no unique constraint on `(user_id, source_path, category)`

**File:** `migrations/versions/b00000000000_baseline.py:94-115`

The `knowledge_entries` table allows duplicate entries for the same user, source path, and category. This could lead to duplicate knowledge entries being embedded and searched.

**Fix:** Add `UniqueConstraint("user_id", "source_path", "category")` or a partial unique index.

---

### DI-HIGH-1: `model_statistics` has unique constraint but `model_variants` does not on `(model_catalog_id)`

**File:** `migrations/versions/b00000000000_baseline.py:727-729`

`model_statistics` correctly has `uq_model_statistics_model_catalog_id`. But `model_variants` has no constraint preventing multiple variants with the same quantization for the same catalog entry. This is likely intentional (multiple size variants per quantization) but worth noting.

---

### DI-HIGH-2: Cascade delete chain: `User` → `Agent` → `AgentRun` → `AgentStep` / `AgentFeedback`

**File:** `backend/app/models/agent.py`

The cascade chain is: `User` → `agents` (CASCADE) → `Agent.runs` (CASCADE) → `AgentRun.steps` (CASCADE) and `AgentRun.feedback` (CASCADE).

Deleting a user cascades to: agents → agent_runs → agent_steps + agent_feedback. This is correct but creates deep cascade chains. A single user deletion could trigger thousands of row deletions.

---

### DI-MED-1: `SyncState.config_json` nullable but ORM default is `dict`

**File:** `backend/app/models/sync_state.py:27`

```python
config_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
```

The type is `dict | None` but the Python default is `dict`. If `config_json` is not provided, it will be `{}` (not `None`). But the column allows NULL, so explicit `None` values are possible.

---

### DI-MED-2: `EmbeddingCache` has no TTL enforcement mechanism

**File:** `backend/app/models/embedding_cache.py:26`

```python
ttl_seconds: Mapped[int] = mapped_column(Integer, default=2592000, nullable=False)
```

The `ttl_seconds` column stores TTL but there's no scheduled job or query filter to evict expired entries. The cache will grow unbounded.

---

### DI-LOW-1: `model_variants` has redundant/overlapping columns

**File:** `migrations/versions/b00000000000_baseline.py:514-555`

| Column pair | Overlap |
|------------|---------|
| `architecture` + `quantization_bits` | `architecture` appears twice (lines 443, 543) |
| `bits_per_param` + `quantization_bits` | Same concept, different names |
| `quality_multiplier` + `quality_score` | Overlapping quality metrics |

---

## Part 6: Database Configuration

### CFG-MED-1: `SessionLocal` uses dynamic session factory pattern

**File:** `backend/app/db/session.py:26-36`

`DynamicSessionLocal` is a callable class that creates sessions on demand. This is unusual — most FastAPI projects use a simple `sessionmaker` instance. The pattern works but adds indirection.

---

### CFG-MED-2: Engine pool settings may be too conservative for production

**File:** `backend/app/db/bootstrap.py:52-59`

```python
pool_size=5
max_overflow=10
pool_timeout=30
pool_recycle=3600
```

`pool_size=5` with `max_overflow=10` gives a maximum of 15 concurrent connections. For a multi-user production system, this may be insufficient. `pool_recycle=3600` (1 hour) is aggressive — PostgreSQL default `idle_in_transaction_session_timeout` is typically 60s.

---

### CFG-LOW-1: `bootstrap_database()` runs migrations at import time

**File:** `backend/app/db/bootstrap.py:64-73`

```python
def bootstrap_database() -> None:
    with _bootstrap_lock:
        run_migrations()
        _create_engine()
```

This is called during app startup. Running migrations during startup is common but means:
- Startup fails if migration fails
- No rollback mechanism if migration partially succeeds
- Multiple workers could race (mitigated by `_bootstrap_lock`)

---

## Part 7: Fix Priority

### Phase 1: Critical (Fix immediately)

| # | Issue | Impact |
|---|-------|--------|
| 1 | MOD-CRIT-1: `auth_events.metadata_json` JSONB/JSON mismatch | Query operators may silently fail |
| 2 | M-CRIT-2: Missing `server_default` on 15+ timestamps | INSERT failures in bulk/raw SQL |
| 3 | SCH-CRIT-1: `AgentInfo.tools` field name mismatch | Agent tools data lost in API responses |
| 4 | DI-CRIT-1: `knowledge_entries` missing unique constraint | Duplicate knowledge entries |
| 5 | M-MED-3: `indexing_configs.user_id` FK missing `ondelete` | User deletion FK violations |

### Phase 2: High (Fix soon)

| # | Issue | Impact |
|---|-------|--------|
| 6 | MOD-HIGH-1: `ModelVariant` FKs missing `ondelete` | Provider deletion FK violations |
| 7 | MOD-HIGH-2: `ModelDownload`/`ModelUsage` FKs missing `ondelete` | User/variant deletion FK violations |
| 8 | MOD-HIGH-3: `Agent.user` missing `back_populates` | ORM navigation breaks |
| 9 | MOD-HIGH-4: `backref` usage in 3 relationships | Untyped reverse sides |
| 10 | SCH-HIGH-1-4: 4 schema-ORM field name mismatches | Data loss in API responses |
| 11 | IDX-HIGH-1: 3 FK columns missing indexes in migration | Slow JOIN queries |
| 12 | M-HIGH-1-3: Raw SQL, missing guards in migration | Portability + reliability |

### Phase 3: Medium (Fix when touching these areas)

| # | Issue | Impact |
|---|-------|--------|
| 13 | MOD-MED-1: `CodeChunk` missing unique constraint | Duplicate chunks possible |
| 14 | MOD-MED-3: DateTime tz-aware/naive inconsistency | Comparison bugs |
| 15 | MOD-MED-4: Default value mechanism inconsistency | Bulk insert failures |
| 16 | IDX-MED-1: `User.deleted_at` missing index | Slow soft-delete queries |
| 17 | SCH-MED-1: `parameter_count` type mismatch (6 schemas) | Type-safety gap |
| 18 | M-MED-1-2: Migration nullable/unique mismatches | Schema drift |

### Phase 4: Low (Fix opportunistically)

| # | Issue | Impact |
|---|-------|--------|
| 19 | MOD-LOW-1-4: Minor model issues | Code quality |
| 20 | SCH-LOW-1-2: Empty/weak schemas | API completeness |
| 21 | IDX-LOW-1: Hardcoded English text search | i18n gap |
| 22 | DI-LOW-1: Redundant columns in `model_variants` | Schema debt |
| 23 | M-LOW-1-3: TIMESTAMP, naming, duplication | Maintenance clarity |

---

## Part 8: Schema-ORM Alignment Matrix

| ORM Model | Has Pydantic Schema? | Schema Name | Field Mismatches |
|-----------|---------------------|-------------|-----------------|
| User | Yes | UserResponse | `storage_root`, `data_path`, `personal_storage_path` not in ORM |
| Conversation | Yes | ConversationResponse | None |
| ConversationMessage | Yes | ConversationMessageResponse | None |
| Agent | Yes | AgentInfo | `tools` vs `tools_json` |
| AgentRun | Yes | AgentRunInfo | `input` vs `input_text` |
| AgentStep | Yes | AgentStepInfo | `action_input` vs `action_input_json`, missing `observation` |
| AgentFeedback | Yes | AgentFeedbackInfo | None |
| Notification | Yes | NotificationResponse | None |
| Document | No dedicated schema | — | — |
| DocumentChunk | No dedicated schema | — | — |
| GraphNode | Partial (in repository.py) | — | Via `GraphGetResponse.nodes: list[dict]` |
| GraphEdge | Partial (in repository.py) | — | Via `GraphGetResponse.edges: list[dict]` |
| ModelCatalog | Yes | ModelCatalogEntry | `model_type`, `size_bytes`, `downloaded`, `hardware_requirements` not in ORM |
| ModelVariant | Yes | ModelVariantInfo | None |
| ModelDownload | No dedicated schema | — | — |
| ModelUsage | No dedicated schema | — | — |
| Provider | No dedicated schema | — | — |
| ProviderModel | No dedicated schema | — | — |
| RepoIndex | Yes | RepoInfo | None |
| CodeChunk | No dedicated schema | — | — |
| IndexedFile | No dedicated schema | — | — |
| PathIndex | No dedicated schema | — | — |
| IndexingConfig | Yes | IndexingConfigInfo | None |
| StorageRegistry | No dedicated schema | — | — |
| EmbeddingCache | No dedicated schema | — | — |
| LongTermMemory | No dedicated schema | — | — |
| KnowledgeEntry | No dedicated schema | — | — |
| SyncState | No dedicated schema | — | — |
| UserModelSettings | Yes | ModelSettingsResponse | None |
| AuthEvent | No dedicated schema | — | — |

---

## Part 9: Migration Health Summary

| Check | Result |
|-------|--------|
| Migration chain integrity | PASS — Single baseline, no chain conflicts |
| Duplicate migrations | NONE — All 27 prior migrations squashed |
| Missing downgrades | PARTIAL — Downgrade exists but missing guards |
| Circular dependencies | NONE |
| Missing head revision | PASS — `b00000000000` is sole head |
| Downgrade correctness | PASS — Drop order is correct for all FK pairs |
| Schema parity | DISCREPANCIES — nullable, unique, JSONB/JSON mismatches |
| Table coverage | 1 orphan table (`knowledge_entries`) — model exists in `intelligence/models.py` |

---

## Part 10: Index Health Summary

| Table | FK Columns Without Index (migration) | Notes |
|-------|-------------------------------------|-------|
| `model_variants` | `provider_id`, `provider_model_id` | ORM has `index=True` but migration doesn't create them |
| `sync_states` | `repo_id` | ORM has `index=True` but migration doesn't create it |
| `users` | — | Missing index on `deleted_at` (soft-delete column) |

**Redundant indexes:** None found (corrected from v1).

**Naming inconsistencies:** 3 composite indexes have different names between migration and ORM model.
