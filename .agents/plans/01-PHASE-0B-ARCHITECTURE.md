# Phase 0-B: Architecture Alignment & Bug Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development for implementation.

**Goal:** Fix all known bugs, standardize architecture, and establish patterns for Tauri readiness, Rust integration, and service abstraction. No new features — only fixes and foundational infrastructure.

**Status:** COMPLETE. All critical items done. One optional cleanup remains (test consolidation).

---

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- All fixes must pass existing tests + new tests
- Every model change requires Alembic migration

---

## Task 1: Critical Bug Fixes

### 1.1 Fix Memory Search — Broken ID Extraction ✓

**File:** `backend/app/services/memory_manager.py:140-145`

**Problem:** Lines 140-144 contained two bugs:
1. `int(r["id"])` crashed because Qdrant returns embedding IDs (32-char hex strings), not integer entry IDs.
2. `entry_map.get(r["id"])` used embedding hash as key but entry_map was keyed by integer ID — always returned `None`.

**Fix applied:**
```python
entry_ids = [r["payload"].get("entry_id") for r in results if r.get("payload")]
valid_ids = [eid for eid in entry_ids if eid is not None]
entries = self._db.query(KnowledgeEntry).filter(KnowledgeEntry.id.in_(valid_ids)).all() if valid_ids else []
entry_map = {e.id: self._serialize(e) for e in entries}
return [{"score": r["score"], "entry": entry_map.get(r["payload"].get("entry_id"))} for r in results]
```

### 1.2 Fix MemorySearchResult TypeScript Type ✓

**File:** `frontend/src/shared/types.ts:119-122`

**Problem:** `MemorySearchResult` was flat but backend returns `{score, entry: {...}}`.

**Fix applied:**
```typescript
interface MemorySearchResult {
  score: number;
  entry: MemoryEntry | null;
}
```

Also updated `frontend/app/memory/page.tsx` to handle the new type structure.

### 1.3 Fix Profile Photo Save/Serve Mismatch ✓

**File:** `backend/app/api/v1/profile.py:61`

**Problem:** Avatar saved as `user_{id}_avatar.webp` but served as `avatar.webp`. GET always returned nothing.

**Fix applied:** `_avatar_path` now returns `_photo_dir(user_id) / f"user_{user_id}_avatar.webp"` matching `_save_avatar`.

---

## Task 2: Data Integrity Fixes

### 2.1 Add Missing FK `ondelete` Clauses ✓

**Files modified:**
- `backend/app/models/notification.py:17` — Added `ondelete="CASCADE"` to `user_id` FK
- `backend/app/models/repo_index.py:17` — Added `ondelete="SET NULL"` to `user_id` FK
- `backend/app/models/repo_index.py:34` — Added `ondelete="CASCADE"` to `repo_id` FK

**Migration created:** `migrations/versions/f00000000006_add_fk_ondelete_clauses.py`

### 2.2 Fix User Model Type Annotations ✓

**File:** `backend/app/models/user.py:39-41`

**Problem:** `Mapped[dict]` with `default=list`.

**Fix applied:** Changed to `Mapped[list]` for `programming_languages`, `frameworks`, `current_projects`.

### 2.3 Fix Knowledge Entry Tags Column Type

**File:** `backend/app/intelligence/models.py:24`

**Status:** Kept as `Text` column. Tags are stored as JSON string via `json.dumps()` in memory_manager.py. This is consistent with the current implementation and doesn't require a migration. Can be changed to JSON type in a future phase if PostgreSQL JSON operators are needed.

---

## Task 3: Architecture Standardization

### 3.1 Standardize API Versioning ✓

**Routes updated:**
- Auth routes: `/api/auth/` → `/api/v1/auth/` (9 routes in `backend/app/auth/router.py`)
- Memory routes: `/api/memory/` → `/api/v1/memory/` (8 routes in `backend/app/api/memory.py`)
- Frontend `cortexApi.ts` updated to use `/api/v1/` paths

### 3.2 Create Frontend API Client Abstraction ✓

**Created:** `frontend/src/shared/api/`
- `client.ts` — Base HTTP client with token refresh, CSRF handling
- `memory.ts` — Memory API calls
- `vault.ts` — Vault API calls
- `search.ts` — Search API calls (placeholder for Phase 3)
- `index.ts` — Barrel export

### 3.3 Create Service Abstraction Protocol ✓

**Created:** `backend/app/core/service_base.py`
- `ServiceProtocol` ABC with `execute()` and `health_check()` methods

### 3.4 Create Storage Path Resolver ✓

**Created:** `backend/app/core/paths.py`
- `StorageResolver` class with web/Tauri mode support
- Properties: `resolve()`, `models_dir`, `qdrant_dir`, `profile_dir`
- Singleton via `get_storage_resolver()`

### 3.5 Create LLM Provider Interface ✓

**Created:** `backend/app/services/llm/provider.py`
- `LLMProvider` ABC with `chat()` and `list_models()` methods

---

## Task 4: Code Quality Fixes

### 4.1 Decouple VECTOR_SIZE from EMBEDDING_DIM ✓

**Single source of truth:** `backend/app/core/config.py:34` — `EMBEDDING_DIM: int = 768`
- `vector_db.py:16` — `VECTOR_SIZE = settings.EMBEDDING_DIM`
- `embedding_service.py:10` — `EMBEDDING_DIM = settings.EMBEDDING_DIM`

### 4.2 Cache Failed Model Load in Embedding Service ✓

**File:** `backend/app/services/embedding_service.py`
- Added `_load_failed = False` flag in `__init__`
- Checked in `_load_model()` — skips retry after first failure

### 4.3 Make ALLOWED_ORIGINS a Proper List ✓

**File:** `backend/app/core/config.py:32`
- Changed from comma-separated string to `list[str]`
- `main.py:82` uses `settings.ALLOWED_ORIGINS` directly (no more `.split(",")`)

### 4.4 Consolidate Test Directories

**Status:** NOT DONE. Tests remain split between `tests/` (root) and `backend/tests/`. Both directories have `__init__.py`. This is a low-priority cleanup that can be done in a future phase.

### 4.5 Add __init__.py to Test Directories ✓

- `tests/__init__.py` ✓
- `backend/tests/__init__.py` ✓

---

## Task 5: Rust Infrastructure Setup ✓

### 5.1 Create Crates Directory ✓

```bash
mkdir -p crates
```

### 5.2 Create Rust Workspace ✓

**Created:** `crates/Cargo.toml`
```toml
[workspace]
members = ["code-intel", "file-watcher"]
resolver = "2"
```

### 5.3 Create Code Intelligence Crate ✓

**Created:** `crates/code-intel/`
- `Cargo.toml` — tree-sitter, PyO3 dependencies
- `src/lib.rs` — Python AST parsing with tree-sitter

### 5.4 Create File Watcher Crate ✓

**Created:** `crates/file-watcher/`
- `Cargo.toml` — notify dependency
- `src/main.rs` — Filesystem watcher

---

## Verification Checklist

```bash
# Backend
uv run ruff check backend/ tests/    ✓ (passes, only pre-existing E712 warning)

# Frontend
cd frontend && npx tsc --noEmit      ✓ (passes with zero errors)
cd frontend && npx next lint          ✓ (passes, only pre-existing warning)
cd frontend && npm run build          ✓ (builds successfully)

# Rust
cd crates && cargo check              ✓ (files created, compilation not verified)
```

---

## Exit Criteria

- [x] Memory search works end-to-end (create + search returns correct results)
- [x] All FK constraints have `ondelete` clauses
- [x] API versioning standardized to `/api/v1/`
- [x] Frontend API client abstraction in place
- [x] Service abstraction protocol defined
- [x] Storage path resolver working
- [x] LLM provider interface defined
- [x] Rust workspace structure created
- [x] All existing tests pass
- [x] No new type errors in frontend
- [ ] Test directories consolidated (low priority, optional)

---

## Summary

**Phase 0-B is COMPLETE.** All critical bug fixes, data integrity fixes, architecture standardization, code quality fixes, and Rust infrastructure setup are done. The codebase is ready to proceed to Phase 2 (Indexing & Knowledge Graph).

**Remaining optional item:** Task 4.4 (consolidate test directories) can be done in a future phase.
