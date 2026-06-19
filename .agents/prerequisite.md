# Cortex Prerequisite: Repository Alignment

> **Purpose:** Bridge between current repository state and the 90-day roadmap.
> Complete every item in this document before proceeding to Phase 2 (Memory & Indexing).
>
> **Audit: 2026-06-19 — See status checkboxes below for completion state.**

---

## Current State Summary

**Phase 1 Complete:** Auth, vault, profile, GitHub linking, admin, vault file browser.
**Phase 2 Not Started:** No vector DB, no embeddings, no agents, no intelligence.

| System | Status | Notes |
|--------|--------|-------|
| Auth | Working | JWT + Argon2, refresh rotation, rate limiting |
| Vault | Working | AES-256-GCM encryption, two-password model |
| Profile | Working | Avatar upload, GitHub linking |
| Memory API | Placeholder | `knowledge_entries` table exists, no vector search |
| Frontend | Working | Next.js 15, dark theme, vault file browser |
| Tests | 81 passing | SQLite in tests, PostgreSQL in production |
| CI/CD | Working | GitHub Actions, lint/test/build |

---

## Category 1: Critical Fixes

### 1.1 Align Plans with Current Codebase

**Problem:** All 6 planning files assume `apps/backend/` and `apps/frontend/` structure. Current codebase uses `backend/` and `frontend/` at root.

**Impact:** Following plans literally creates duplicate code or requires restructuring.

**Resolution:** Rewrite all planning files to use current file paths:
- `backend/app/...` (not `apps/backend/app/...`)
- `frontend/app/...` (not `apps/frontend/app/...`)
- `frontend/src/shared/...` (not `apps/frontend/src/shared/...`)

**Acceptance Criteria:**
- [x] All plan file paths match current repository structure
- [x] Plans reference existing code, not recreations
- [x] No plan creates files that already exist

### 1.2 Add Missing Foreign Key Constraints

**Problem:** `user_storage_registry.user_id` has no FK constraint. `auth_events.user_id` FK exists in migration but not in ORM model.

**Impact:** Orphaned rows possible, relationship mappers can't traverse.

**Resolution:**
1. Add `ForeignKey("users.id")` to `AuthEvent.user_id` in model
2. Add `ForeignKey("users.id", ondelete="CASCADE")` to `StorageRegistry.user_id`
3. Create migration to add FK constraints
4. Backfill any orphaned rows

**Acceptance Criteria:**
- [x] Both models have FK declarations (with `ondelete` matching migrations)
- [x] Migration adds constraints (both FKs exist: `auth_events` in `d00000000004`, `storage_registry` in `e00000000005`)
- [x] Orphaned rows cleaned up (DELETE before FK in migration)
- [x] Tests pass with new constraints

### 1.3 Enable TypeScript Strict Mode

**Problem:** `tsconfig.json` has `strict: false`. No null checks, no implicit any detection.

**Impact:** Type errors accumulate silently, runtime bugs.

**Resolution:** Enable strict mode incrementally:
1. Enable `strictNullChecks` first
2. Fix all null/undefined errors
3. Enable `strictFunctionTypes`
4. Enable `noImplicitAny`
5. Enable full `strict` mode

**Acceptance Criteria:**
- [x] `strict: true` in tsconfig.json
- [x] `npx tsc --noEmit` passes with zero errors
- [x] CI enforces type checking

---

## Category 2: Required Refactors

### 2.1 Decompose Monolithic Vault Component

**Problem:** `frontend/app/vault/page.tsx` is 1735 lines with 35+ useState hooks.

**Impact:** Unmaintainable, untestable, difficult to modify.

**Resolution:** Extract into focused components:
- `VaultLayout.tsx` — 3-panel resizable shell
- `VaultSidebar.tsx` — Folder tree + categories
- `VaultFileList.tsx` — Table/list/grid views
- `VaultProperties.tsx` — Right panel (metadata, tags)
- `VaultToolbar.tsx` — Upload, new folder, search, view toggle
- `VaultModals.tsx` — Folder creation, rename, delete, export, rekey
- `VaultLockScreen.tsx` — Lock/unlock UI
- `useVaultState.ts` — Custom hook for vault state management

**Acceptance Criteria:**
- [x] `vault/page.tsx` < 200 lines (now 48 lines)
- [x] Most components < 300 lines
- [x] State logic extracted to custom hooks (decomposed into 7 focused hooks + utils)
- [x] All existing functionality preserved
- [x] No visual changes

### 2.2 Consolidate Token Functions

**Problem:** `core/security.py` and `core/tokens.py` both provide token functions. `tokens.py` is a thin wrapper.

**Impact:** Confusion about which to use, unnecessary indirection.

**Resolution:**
1. Move all token logic to `core/security.py`
2. Update all imports to use `core/security.py`
3. Delete `core/tokens.py`
4. Update tests

**Acceptance Criteria:**
- [x] Single source of truth for token functions in `core/security.py`
- [x] No import of `core/tokens.py` anywhere
- [x] All tests pass

### 2.3 Make Auth Service Fully Async

**Problem:** Auth service has sync functions that bridge to async Redis via `redis_cache.run_sync()`.

**Impact:** Creates isolated event loops per call, performance overhead.

**Resolution:**
1. Convert `register_user`, `login_user_service` to async
2. Use `await` for Redis operations directly
3. Update route handlers to use async service methods

**Acceptance Criteria:**
- [x] All auth service functions are async
- [x] No `run_sync()` calls in auth path
- [x] All tests pass

### 2.4 Migrate JSON Columns to JSONB

**Problem:** `handles_json`, `preferences_json`, `metadata_json` stored as Text.

**Impact:** No database-level JSON validation, can't use PostgreSQL JSONB operators.

**Resolution:**
1. Create migration to alter columns to JSONB
2. Update models to use `JSONB` type
3. Update any manual JSON serialization/deserialization

**Acceptance Criteria:**
- [x] Migration converts Text to JSONB (PostgreSQL `jsonb` type)
- [x] ORM uses cross-dialect `JSON` type (maps to JSONB on PG, works on SQLite in tests)
- [x] JSON queries work with `->` / `->>` operators (tested with SQLAlchemy JSON accessor)
- [x] All tests pass

### 2.5 Fix Profile Photo Storage Location

**Problem:** Photos stored in `CortexMemory/photos/{user_id}/` instead of `<storage_root>/profile/`.

**Impact:** Violates storage boundary principle from vision.

**Resolution:**
1. Create migration to move existing photos
2. Update photo upload endpoint to use `<storage_root>/profile/`
3. Update photo retrieval to check new location
4. Keep backward compatibility for existing photos

**Acceptance Criteria:**
- [x] New photos stored in `<storage_root>/profile/`
- [x] Existing photos preserved (backward compatible fallback to `CortexMemory/photos/{user_id}/`)
- [x] Public photo URL still works
- [x] All tests pass

---

## Category 3: Missing Foundations

### 3.1 Add Task Queue (Required for Phase 2+)

**Problem:** No background job processing. Indexing, embeddings, agents would block API.

**Impact:** Long-running operations timeout or block event loop.

**Resolution:**
1. Add `arq` dependency (async Redis-based task queue)
2. Create `backend/app/tasks/` module
3. Create worker process configuration
4. Add task definitions for indexing, embeddings, agents

**Acceptance Criteria:**
- [x] `arq` in dependencies
- [x] `backend/app/tasks/` module exists
- [x] Worker can be started via `make worker`
- [x] Example task works end-to-end (`backend/app/tasks/worker.py` with `sample_task` + `__main__` demo)

### 3.2 Add Vector Database Integration (Required for Phase 2)

**Problem:** No vector DB. Plans reference `VectorDB` class that doesn't exist.

**Impact:** Can't do semantic search or embeddings.

**Resolution:**
1. Add `qdrant-client` dependency
2. Create `backend/app/core/vector_db.py` with `VectorDB` class
3. Implement `upsert()`, `search()`, `delete()`, `list_collections()`
4. Add Qdrant to docker-compose.yml

**Acceptance Criteria:**
- [x] `qdrant-client` in dependencies
- [x] `VectorDB` class with `upsert()`, `search()`, `delete()`, `list_collections()`
- [x] Qdrant in docker-compose.yml
- [x] Unit tests for VectorDB (11 tests)

### 3.3 Add Embedding Service (Required for Phase 2)

**Problem:** No embedding generation. Plans reference `EmbeddingService` that doesn't exist.

**Impact:** Can't generate embeddings for vector search.

**Resolution:**
1. Add `onnxruntime` dependency
2. Create `backend/app/services/embedding_service.py`
3. Implement BGE-M3 ONNX model loading
4. Add mock fallback for testing

**Acceptance Criteria:**
- [x] `onnxruntime` in dependencies
- [x] `EmbeddingService` class with `embed()` and `embed_batch()`
- [x] Mock fallback for tests
- [x] Unit tests (13 tests)

### 3.4 Add WebSocket Support (Required for Phase 3+)

**Problem:** No WebSocket endpoints. Agents need streaming output.

**Impact:** Poor UX for long-running operations.

**Resolution:**
1. Add WebSocket endpoint to FastAPI
2. Create connection manager for broadcasting
3. Implement agent output streaming

**Acceptance Criteria:**
- [x] `/ws` endpoint exists
- [x] Connection manager handles multiple clients
- [x] Example streaming works (`/ws/demo` with echo + stream modes)

### 3.5 Add Global Rate Limiting (Required for Production)

**Problem:** Rate limiting only on login endpoint.

**Impact:** API abuse possible on other endpoints.

**Resolution:**
1. Create rate limiting middleware
2. Apply to all endpoints with configurable limits
3. Use Redis for distributed rate limiting

**Acceptance Criteria:**
- [x] Rate limiting on all endpoints (with exemptions for auth, health, metrics, ws)
- [x] Configurable via environment variables
- [x] Fails open when Redis unavailable

---

## Category 4: Security Improvements

### 4.1 Move JWT to httpOnly Cookies

**Problem:** JWT tokens in sessionStorage (XSS risk).

**Impact:** Account compromise via XSS.

**Resolution:**
1. Set access token in httpOnly cookie on login
2. Set refresh token in httpOnly cookie on login
3. Update frontend to use cookies instead of sessionStorage
4. Add CSRF protection

**Acceptance Criteria:**
- [x] Tokens in httpOnly cookies
- [x] No tokens in sessionStorage (user object only)
- [x] CSRF tokens on state-changing requests
- [x] All auth flows work

### 4.2 Tighten CSP Headers

**Problem:** CSP allows `unsafe-inline` and `unsafe-eval`.

**Impact:** XSS attacks easier.

**Resolution:**
1. Remove `unsafe-inline` from `script-src`
2. Remove `unsafe-eval` from `script-src`
3. Use nonces for inline scripts if needed

**Acceptance Criteria:**
- [x] No `unsafe-eval` in CSP
- [x] No `unsafe-inline` in `script-src` (removed; `style-src` retains `unsafe-inline` for Next.js inline styles — unavoidable without nonce injection at server-render level)
- [x] All functionality works

### 4.3 Add Soft Delete for Accounts

**Problem:** Account deletion is destructive (`shutil.rmtree`).

**Impact:** Accidental deletion is irreversible.

**Resolution:**
1. Add `deleted_at` timestamp to users table
2. Soft delete: set timestamp, don't remove data
3. Add grace period (7 days) before permanent deletion
4. Add account recovery endpoint

**Acceptance Criteria:**
- [x] `deleted_at` column added
- [x] Soft delete implemented (`DELETE /api/auth/me` sets `deleted_at`)
- [x] Recovery possible within grace period (`POST /api/auth/restore`)
- [x] All tests pass

---

## Category 5: Production Readiness

### 5.1 Add TLS/HTTPS Configuration

**Problem:** No TLS configuration.

**Impact:** All traffic in plaintext.

**Resolution:**
1. Add TLS termination configuration
2. Document nginx/Caddy setup
3. Add HTTPS redirect middleware

**Acceptance Criteria:**
- [x] TLS configuration documented
- [x] HTTPS redirect works (opt-in via `HTTPS_REDIRECT_ENABLED`)
- [x] Certificate loading documented (`docs/TLS.md` with nginx/Caddy/self-signed options)

### 5.2 Add Structured Logging with Correlation IDs

**Problem:** Basic structlog, no correlation IDs.

**Impact:** Difficult to trace requests in production.

**Resolution:**
1. Add correlation ID to request context
2. Include correlation ID in all log entries
3. Add request ID to response headers

**Acceptance Criteria:**
- [x] Correlation ID in all logs (`RequestIdFilter` injects into all log records via logging filter)
- [x] Request ID in response headers (`x-request-id`)
- [x] Logs parseable by aggregators (structured format with request_id field)

### 5.3 Add Metrics Endpoint

**Problem:** No metrics/monitoring.

**Impact:** Can't monitor system health.

**Resolution:**
1. Add `/metrics` endpoint
2. Expose request count, latency, error rates
3. Add database connection pool metrics

**Acceptance Criteria:**
- [x] `/metrics` endpoint exists
- [x] Prometheus-compatible format
- [x] Key metrics exposed (request count, error rate, average/max latency, uptime, RSS memory)

### 5.4 Add Backup Strategy

**Problem:** No backup strategy.

**Impact:** Data loss on failure.

**Resolution:**
1. Document PostgreSQL backup procedure
2. Add backup script for CortexMemory
3. Document restore procedure

**Acceptance Criteria:**
- [x] Backup script exists (`scripts/backup.sh` with DB dump, file archive, rotation)
- [x] Restore procedure documented
- [x] Backup/restore documented with commands (`docs/BACKUP.md` + `scripts/backup.sh` verified executable)

### 5.5 Add Frontend Test Framework

**Problem:** No frontend tests.

**Impact:** Zero test coverage for UI.

**Resolution:**
1. Add Vitest + React Testing Library
2. Create tests for critical components
3. Add to CI pipeline

**Acceptance Criteria:**
- [x] Vitest configured
- [x] Tests for auth pages (login + signup wizard flow tests added)
- [x] CI runs frontend tests (vitest step added to CI)

---

## Category 6: Plan File Updates

### 6.1 Update All Plan File Paths

Every plan file must be updated to use current codebase paths:

| Old Path | New Path |
|----------|----------|
| `apps/backend/app/...` | `backend/app/...` |
| `apps/frontend/app/...` | `frontend/app/...` |
| `apps/frontend/src/shared/...` | `frontend/src/shared/...` |

### 6.2 Update Plan Dependencies

Plans must reference existing code interfaces, not assume they exist:

**Week 3-4 (Memory) must reference:**
- `backend/app/core/config.py` — `settings` object
- `backend/app/core/db.py` — `get_db()` dependency
- `backend/app/models/user.py` — `User` model
- `backend/app/auth/` — Auth system

**Week 5-6 (Indexing) must reference:**
- `backend/app/core/vector_db.py` — From prerequisite 3.2
- `backend/app/services/embedding_service.py` — From prerequisite 3.3

**Week 7-8 (Agents) must reference:**
- `backend/app/tasks/` — From prerequisite 3.1
- `backend/app/core/vector_db.py` — From prerequisite 3.2

### 6.3 Add Migration Steps to Each Plan

Every plan that creates new tables must include:
1. Model definition
2. Alembic migration generation
3. Migration application
4. Test schema validation

### 6.4 Add API Versioning to Plans

All new endpoints must follow:
- Version prefix: `/api/v1/`
- Consistent naming: `/api/v1/{resource}`
- Auth requirements documented

---

## Implementation Order

Complete prerequisites in this order:

```
Week 0: Critical Fixes (1.1 - 1.3)
    ↓
Week 1: Required Refactors (2.1 - 2.5)
    ↓
Week 2: Missing Foundations (3.1 - 3.5)
    ↓
Week 3: Security Improvements (4.1 - 4.3)
    ↓
Week 4: Production Readiness (5.1 - 5.5)
    ↓
Week 5: Plan File Updates (6.1 - 6.4)
    ↓
Ready for Phase 2 (Memory & Indexing)
```

---

## Dependencies

```
1.1 (Plan Alignment) → All other tasks
1.2 (FK Constraints) → 2.1 (Vault Decompose)
1.3 (TypeScript Strict) → 2.1 (Vault Decompose)
2.1 (Vault Decompose) → Frontend work
2.2 (Token Consolidation) → 2.3 (Async Auth)
2.3 (Async Auth) → 3.1 (Task Queue)
3.1 (Task Queue) → 3.2 (Vector DB), 3.3 (Embeddings)
3.2 (Vector DB) → Week 3-4 Plan
3.3 (Embeddings) → Week 3-4 Plan
3.4 (WebSocket) → Week 7-8 Plan
3.5 (Rate Limiting) → Production deployment
4.1 (JWT Cookies) → 4.2 (CSP Headers)
4.3 (Soft Delete) → Production deployment
5.1 (TLS) → Production deployment
5.2 (Logging) → Production deployment
5.3 (Metrics) → Production deployment
5.4 (Backups) → Production deployment
5.5 (Frontend Tests) → All frontend work
```

---

## Acceptance Criteria Summary

Before proceeding to Phase 2, verify:

### Code Quality
- [x] All plan files use current codebase paths
- [x] TypeScript strict mode enabled
- [x] No type errors in frontend (tsc passes)
- [x] No lint errors in backend
- [x] All 81+ tests passing

### Architecture
- [x] FK constraints on all relationships (ORM models match migrations)
- [x] JSONB for JSON columns (DB migration + cross-dialect `JSON` + query tests)
- [x] Task queue operational (`arq` + `backend/app/tasks/`)
- [x] Vector DB integrated (`qdrant-client` + `VectorDB` class)
- [x] Embedding service working (`onnxruntime` + `EmbeddingService` class)
- [x] WebSocket endpoint available (`/ws` + `ConnectionManager`)

### Security
- [x] JWT in httpOnly cookies
- [~] CSP headers tightened (script-src good; style-src `unsafe-inline` for Next.js)
- [x] Global rate limiting (`RateLimitMiddleware`)
- [x] Soft delete for accounts (endpoint sets `deleted_at`, restore available)

### Production
- [x] TLS configuration documented (`docs/TLS.md`)
- [x] Structured logging with correlation IDs (`RequestIdFilter` injects into all log records)
- [x] Metrics endpoint (`/metrics` with request count, error rate, latency, uptime, RSS)
- [x] Backup strategy documented + executable (`docs/BACKUP.md` + `scripts/backup.sh`)
- [x] Frontend test framework (Vitest + auth page tests + CI step)

### Documentation
- [x] Context.md updated
- [x] AGENTS.md updated
- [x] README.md updated
- [x] All plans rewritten

---

## Verification Commands

```bash
# Backend
uv run ruff check backend/ tests/
uv run mypy backend/ --ignore-missing-imports
PYTHONPATH=. pytest tests/ -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx next lint
cd frontend && npm run build

# Integration
make test
make lint
```

---

## Notes

1. **This document is the single source of truth** for repository alignment
2. **Complete all items** before starting Phase 2
3. **Update this document** as items are completed
4. **Reference this document** in all planning files
5. **The vision is unchanged** — this is about execution quality
