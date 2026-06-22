# Cortex Database Audit Report

Generated: 2026-06-22

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Migration issues | 1 | 2 | 3 | 4 | 10 |
| Model issues | 3 | 4 | 5 | 5 | 17 |
| Schema mismatches | 0 | 1 | 0 | 2 | 3 |
| **Total** | **4** | **7** | **8** | **11** | **30** |

---

## Part 1: Critical Issues

### C1: `knowledge_entries` table exists in migration but has no ORM model

The baseline migration creates `knowledge_entries` with 12 columns and 5 indexes. No model class exists anywhere in the codebase. The table is orphaned — the app cannot query it via ORM.

**Impact:** Table exists in the database but is completely unused. Wasted storage and migration complexity.

**Fix:** Either create a model class or drop the table via a new migration.

---

### C2: Missing FK constraints in ORM models (present in migration)

Three models define columns as plain `Integer` without `ForeignKey()`, but the migration adds FK constraints:

| Model | Column | Migration FK |
|-------|--------|-------------|
| `Conversation.user_id` | `Integer, nullable=False` | `users.id CASCADE` |
| `Conversation.repo_id` | `Integer, nullable=True` | `repo_indexes.id SET NULL` |
| `LongTermMemory.user_id` | `Integer, nullable=False` | `users.id CASCADE` |

**Impact:** SQLAlchemy relationships, cascades, and referential integrity checks won't work at the ORM level. If `create_all()` is used instead of migrations, these FKs will be missing entirely.

**Fix:** Add `ForeignKey("users.id", ondelete="CASCADE")` etc. to the model definitions.

---

### C3: Baseline migration downgrade has drop-order bug

The `downgrade()` function drops tables in an order that violates FK constraints:

```
Line 890: op.drop_table("provider_models")   # model_variants still references this
Line 892: op.drop_table("providers")          # model_catalog + model_variants reference this
Line 895: op.drop_table("model_variants")     # Drops AFTER its FK targets
```

**Impact:** `alembic downgrade` will fail on PostgreSQL with FK violation errors.

**Fix:** Reorder drops: `model_variants` → `model_catalog` → `model_statistics` → `provider_models` → `sync_jobs` → `providers`.

---

### C4: Baseline migration missing `server_default` on timestamp columns

The consolidated baseline uses bare `sa.TIMESTAMP()` on many NOT NULL timestamp columns without `server_default`. The archived migrations consistently used `server_default=sa.func.now()`. Affected columns include `created_at` on: `knowledge_entries`, `user_storage_registry`, `notifications`, `graph_nodes`, `graph_edges`, `agents`, `agent_runs`, `agent_steps`, `agent_feedback`, `conversations`, `conversation_messages`, `documents`, `document_chunks`, `embedding_cache`, `long_term_memories`.

**Impact:** INSERT failures if application code doesn't explicitly provide values for all these columns.

**Fix:** Add `server_default=sa.func.now()` to all NOT NULL timestamp columns in the baseline.

---

## Part 2: High-Severity Issues

### H1: Missing indexes on FK columns

Every FK column should have an index. These lack one in both model and migration:

| Model | Column | FK Target |
|-------|--------|-----------|
| `ModelVariant` | `provider_id` | `providers.id` |
| `ModelVariant` | `provider_model_id` | `provider_models.id` |
| `ModelDownload` | `model_variant_id` | `model_variants.id` |
| `ModelCatalog` | `primary_provider_id` | `providers.id` |
| `SyncState` | `repo_id` | `repo_indexes.id` |

**Impact:** Queries joining on these FKs will require full table scans.

---

### H2: Redundant index on `AgentRun.user_id`

- Column-level: `index=True` (creates `ix_agent_runs_user_id`)
- `__table_args__`: `Index("idx_agent_runs_user", "user_id")`

Two separate B-tree indexes on the same column. Wastes storage and slows writes.

**Fix:** Remove one of the two indexes.

---

### H3: Missing `ondelete` on `IndexingConfig.user_id` FK

All other user FKs use `CASCADE` or `SET NULL`. `IndexingConfig.user_id` has no `ondelete`. Deleting a user will raise a FK violation error instead of cascading.

**Fix:** Add `ondelete="CASCADE"` to the FK.

---

### H4: Missing `ondelete` on `ModelCatalog.primary_provider_id` FK

No `ondelete` specified. Deleting a provider referenced as a primary provider will fail.

**Fix:** Add `ondelete="SET NULL"` to the FK.

---

### H5: Missing FK indexes declared in model but present in migration

| Model | Column | Migration creates index |
|-------|--------|------------------------|
| `AuthEvent` | `user_id` | `ix_auth_events_user_id` |
| `AgentFeedback` | `user_id` | `ix_agent_feedback_user_id` |

If `create_all()` is used instead of migrations, these indexes won't exist.

**Fix:** Add `index=True` to these columns in the model.

---

### H6: Pydantic schema `AgentStepInfo` field name mismatch with ORM

| Schema field | ORM field | Issue |
|-------------|-----------|-------|
| `input` | `thought` / `action_input_json` | Name mismatch |
| `output` | `observation` | Name mismatch |

Pydantic v2 silently drops `thought`/`action_input_json`/`observation` (not in schema) and defaults `input`/`output` to `None`. All agent reasoning data is lost.

**Fix:** Update `AgentStepInfo` schema to match ORM fields.

---

### H7: Schema discrepancies between baseline and archived migrations

| Table.Column | Baseline | Archived | Impact |
|-------------|----------|----------|--------|
| `model_variants.model_catalog_id` | `nullable=True` | `nullable=False` | Baseline allows NULL |
| `agents.name` | Not unique | `unique=True` | Missing unique constraint |
| Several JSONB columns | No `server_default` | `server_default="[]"` | Missing defaults |

---

## Part 3: Medium-Severity Issues

### M1: Missing soft-delete index on `User.deleted_at`

`deleted_at` is defined but has no index. Any query filtering by `deleted_at` (soft-delete checks) requires a full table scan on `users`.

**Fix:** Add `index=True` to `deleted_at` or a composite index `(deleted_at, id)`.

---

### M2: `CodeChunk` missing unique constraint on `(repo_id, file_path, chunk_index)`

`DocumentChunk` has a unique constraint on `(document_id, chunk_index)`. `CodeChunk` has no equivalent, allowing duplicate chunks.

**Fix:** Add `UniqueConstraint("repo_id", "file_path", "chunk_index")` to `CodeChunk`.

---

### M3: `models/__init__.py` only exports 13 of 28 model classes

Missing exports: User, Agent, AgentRun, AgentStep, AgentFeedback, Conversation, ConversationMessage, Document, DocumentChunk, GraphNode, GraphEdge, Notification, AuthEvent, IndexedFile, PathIndex, RepoIndex, CodeChunk, IndexingConfig, StorageRegistry, LongTermMemory, EmbeddingCache.

---

### M4: `RepoIndex.created_at`/`updated_at` nullable inconsistency

The model doesn't explicitly set `nullable=False`. The migration sets `nullable=True`. Other models use `nullable=False` for timestamps.

---

### M5: `ModelVariant` FK ondelete inconsistency

`model_catalog_id` has `ondelete="CASCADE"`. `provider_id` and `provider_model_id` have no ondelete.

---

## Part 4: Low-Severity Issues

### L1: Pydantic type mismatch — `parameter_count`

| Schema | Type | ORM Type |
|--------|------|----------|
| `ModelCatalogEntry.parameter_count` | `str \| None` | `float \| None` |
| `InstalledVariant.parameter_count` | `str \| None` | `float \| None` |
| `ModelSearchResult.parameter_count` | `str \| None` | `float \| None` |
| `ModelDetailResponse.parameter_count` | `str \| None` | `float \| None` |
| `ModelRecommendation.parameter_count` | `str \| None` | `float \| None` |
| `ModelVariantInfo.parameter_count` | `str \| None` | `float \| None` |

---

### L2: `DateTime` vs `DateTime(timezone=True)` inconsistency

- **Timezone-aware:** ModelCatalog, ModelVariant, ModelDownload, ModelUsage, Provider, ProviderModel, Quantization, HardwareProfile, ModelStatistics, SyncJob, UserModelSettings, SyncState, LongTermMemory
- **Timezone-naive:** User, Agent, AgentRun, AgentStep, AgentFeedback, Conversation, ConversationMessage, Document, DocumentChunk, GraphNode, GraphEdge, Notification, IndexedFile, PathIndex, RepoIndex, CodeChunk, IndexingConfig, StorageRegistry, EmbeddingCache, AuthEvent

This split could cause comparison bugs between tables.

---

### L3: Default value mechanism inconsistency

Some models use Python-side `default=X`, others use `server_default=func.now()` or `server_default="X"`. Python defaults are not applied by bulk inserts or raw SQL.

---

### L4: Migration naming gaps

- Letter `o` skipped: `n00000000014` → `p00000000015`
- Revision `b00000000026` missing: `z00000000025` → `b00000000027`
- `f00000000006a` uses non-standard suffix naming
- Active baseline `b00000000000` reuses `b` prefix from archived migrations

---

### L5: `TIMESTAMP` vs `DateTime(tz=True)` in migration

The consolidated baseline uses `sa.TIMESTAMP()` (no timezone) everywhere. PostgreSQL best practice favors `TIMESTAMPTZ`.

---

### L6: `_safe_execute()` in archived migration silently swallows errors

The archived `b00000000027` wraps all operations in a `_safe_execute()` that catches all exceptions. Genuine errors will be silently ignored.

---

### L7: Missing `if_exists` guards in downgrade

The downgrade uses bare `op.drop_table()` without `if_exists=True`. If upgrade partially fails, downgrade will also fail.

---

## Part 5: Migration Health Summary

| Check | Result |
|-------|--------|
| Migration chain integrity | PASS — Archived chain is linear and complete |
| Duplicate migrations | NONE |
| Missing downgrades | ALL HAVE DOWNGRADES (z00000000025 is partial due to PG enum limitation) |
| Circular dependencies | NONE |
| Missing head revision | PASS — `b00000000000` is sole head |
| Downgrade correctness | FAIL — Drop-order bug in baseline |
| Schema parity | DISCREPANCIES — Baseline missing unique constraint, nullable differences, JSONB defaults |
| Table coverage | 1 orphan table (`knowledge_entries`) with no model |

---

## Part 6: Index Health Summary

| Table | FK Columns Without Index | Notes |
|-------|-------------------------|-------|
| `model_variants` | `provider_id`, `provider_model_id` | H1 |
| `model_downloads` | `model_variant_id` | H1 |
| `model_catalog` | `primary_provider_id` | H1 |
| `sync_states` | `repo_id` | H1 |
| `users` | — | Missing index on `deleted_at` (M1) |

**Redundant indexes:**
| Table | Column | Duplicate Indexes |
|-------|--------|-------------------|
| `agent_runs` | `user_id` | `ix_agent_runs_user_id` + `idx_agent_runs_user` |

---

## Part 7: Fix Priority

### Phase 1: Critical (Fix immediately)

1. Fix baseline downgrade drop-order
2. Add `server_default=sa.func.now()` to all NOT NULL timestamps in baseline
3. Add FK constraints to `Conversation.user_id`, `Conversation.repo_id`, `LongTermMemory.user_id` models
4. Decide fate of `knowledge_entries` table (create model or drop)

### Phase 2: High (Fix soon)

5. Add indexes to 5 FK columns without them
6. Fix `AgentStepInfo` schema field names
7. Fix `AgentRun` redundant index
8. Add `ondelete` to `IndexingConfig.user_id` and `ModelCatalog.primary_provider_id` FKs
9. Add `index=True` to `AuthEvent.user_id` and `AgentFeedback.user_id`
10. Align baseline schema with archived migration (unique constraints, JSONB defaults)

### Phase 3: Medium (Fix when touching these areas)

11. Add index on `User.deleted_at`
12. Add unique constraint to `CodeChunk(repo_id, file_path, chunk_index)`
13. Export all model classes from `__init__.py`
14. Fix nullable inconsistency on `RepoIndex` timestamps
15. Fix `ModelVariant` FK ondelete consistency

### Phase 4: Low (Fix opportunistically)

16. Standardize `parameter_count` type (float in ORM, str in schema)
17. Standardize timezone-aware timestamps across all models
18. Standardize default value mechanism (server_default vs Python default)
19. Fix migration naming gaps
20. Add `if_exists` guards to downgrade
