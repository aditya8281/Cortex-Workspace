# MEDIUM Issues Research Findings

## M-S1: CSRF exemption on vault endpoints
- **Still an issue:** YES
- **File:** `backend/app/core/csrf.py:26`
- **Risk of fix:** LOW
- **Details:** `/api/v1/me/vault/` is in `EXEMPT_PREFIXES`. The comment says "vault endpoints are already protected by session authentication (get_current_user)." However, vault endpoints use `get_current_user` which validates Bearer tokens. If the frontend only uses Bearer tokens for vault, CSRF is irrelevant (CSRF only targets cookie-based auth). The exemption is unnecessary but not dangerous if vault endpoints always require Bearer token.
- **Change:** Remove `/api/v1/me/vault/` from `EXEMPT_PREFIXES`. Vault endpoints already require auth, so CSRF protection adds defense-in-depth for cases where session cookies are used.

---

## M-S3: run.error stores internal messages
- **Still an issue:** NO
- **File:** `backend/app/agents/run_manager.py:168`
- **Risk of fix:** N/A
- **Details:** The code stores `run.error = "Agent execution failed"` (a generic message), NOT the raw exception `str(e)`. The raw exception is only logged via `logger.error`. The SSE event also sends the generic message. This issue was already fixed.

---

## M-S5: WebSocket no per-user limits
- **Still an issue:** YES
- **File:** `backend/app/core/websocket.py`
- **Risk of fix:** LOW
- **Details:** `ConnectionManager` tracks connections per channel (`MAX_CONNECTIONS_PER_CHANNEL = 100`) but has no per-user connection tracking. A single user could open many connections across different channels, exhausting server resources. No `user_id` parameter exists in `connect()`.
- **Change:** Add a `user_id` parameter to `connect()`. Track connections per user with a `dict[int, set[WebSocket]]`. Enforce a `MAX_CONNECTIONS_PER_USER` limit (e.g., 10). Reject connections when exceeded.

---

## M-S6: CORS no production origins
- **Still an issue:** YES
- **File:** `backend/app/core/config.py:30-37`
- **Risk of fix:** MEDIUM
- **Details:** `ALLOWED_ORIGINS` is hardcoded to localhost-only URLs. There is no environment-based override for production deployments. For production, the frontend would be served from a real domain.
- **Change:** Make `ALLOWED_ORIGINS` configurable via environment variable (e.g., `CORS_ORIGINS` env var parsed as comma-separated list). Default to the current localhost list for development.

---

## M-S8: validate_storage_path not called
- **Still an issue:** YES
- **File:** `backend/app/services/storage_registry.py:17-37`
- **Risk of fix:** LOW
- **Details:** `register_user_storage()` stores the path directly without calling `validate_storage_path()`. Validation only happens in `auth/service.py:49`. If `register_user_storage` is called from any other code path (e.g., admin tools, tests), the path is unvalidated.
- **Change:** Add `validate_storage_path(storage_root)` call at the beginning of `register_user_storage()` before creating the entry.

---

## M-C1: Search nullable fields
- **Still an issue:** NO
- **File:** Backend `backend/app/api/v1/search.py:47-54`, Frontend `frontend/src/shared/types.ts:233-241`
- **Risk of fix:** N/A
- **Details:** Backend `SearchResult` has: `document_id: int | None`, `language: str | None`, `chunk_type: str | None`. Frontend `SearchResult` has: `document_id: number | null`, `language: string | null`, `chunk_type: string | null`. The types are aligned. This issue was already fixed.

---

## M-C4: Agent tools type mismatch
- **Still an issue:** YES (with workaround in place)
- **File:** Backend model `backend/app/models/agent.py:24` (`tools_json: Mapped[str | None]` Text), Backend schema `backend/app/schemas/agent.py:18` (`tools: str | None`), Frontend type `frontend/src/shared/types.ts:341` (`tools: string[]`)
- **Risk of fix:** LOW
- **Details:** DB stores JSON string, API schema declares `tools: str | None`, but frontend type says `tools: string[]`. The frontend API layer (`frontend/src/shared/api/agent.ts:16`) adds a runtime workaround: `typeof a.tools === "string" ? JSON.parse(a.tools) : (a.tools ?? [])`. The type mismatch exists but is handled.
- **Change:** Either (a) change the backend schema to return `list[str] | None` by parsing `tools_json` in a property/validator, or (b) keep as-is since the frontend workaround works. Option (a) is cleaner.

---

## M-D1: CodeChunk missing unique constraint
- **Still an issue:** YES
- **File:** `backend/app/models/repo_index.py:32-48`, Migration `b00000000000_baseline.py:148-167`
- **Risk of fix:** MEDIUM
- **Details:** `CodeChunk` has `repo_id`, `file_path`, and `chunk_index` columns but no unique constraint on `(repo_id, file_path, chunk_index)`. The migration also lacks this constraint. Without it, re-indexing the same repo could create duplicate chunks for the same file position.
- **Change:** Add `UniqueConstraint("repo_id", "file_path", "chunk_index")` to `CodeChunk.__table_args__`. Create a new Alembic migration to add the constraint. Need to deduplicate existing data first.

---

## M-D2: DateTime tz-aware/naive inconsistency
- **Still an issue:** YES
- **Files:** Multiple models use `func.now()` (naive), while `run_manager.py:169` uses `datetime.now(timezone.utc)` (tz-aware)
- **Risk of fix:** HIGH
- **Details:** Most models (`User`, `Agent`, `Conversation`, etc.) use `server_default=func.now()` which produces naive UTC timestamps. Code like `run_manager.py:169` assigns `datetime.now(timezone.utc)` (tz-aware). Mixing tz-aware and naive datetimes in comparisons or arithmetic raises `TypeError` in Python. The migration also uses `TIMESTAMP()` without timezone.
- **Change:** This is a systemic issue. Options: (a) change all `server_default=func.now()` to `server_default=func.now(timezone=True)` and migrate the DB type to `TIMESTAMPTZ`, or (b) change all runtime code to use naive UTC (`datetime.utcnow()` or `datetime.now(timezone.utc).replace(tzinfo=None)`). Option (b) is safer for backward compatibility. Requires auditing all datetime usage.

---

## M-D4: User.deleted_at missing index
- **Still an issue:** YES
- **File:** Model `backend/app/models/user.py:48` (has `index=True`), Migration `b00000000000_baseline.py:50-79` (NO index created)
- **Risk of fix:** LOW
- **Details:** The User model defines `deleted_at` with `index=True`, but the baseline migration does NOT create an index on `users.deleted_at`. Queries filtering soft-deleted users (e.g., `WHERE deleted_at IS NULL`) will do a full table scan. Note: the `documents` table DOES have `ix_documents_deleted_at` in the migration.
- **Change:** Create a new Alembic migration: `op.create_index("ix_users_deleted_at", "users", ["deleted_at"])`.

---

## M-Q3: Missing input validation
- **Still an issue:** YES
- **Files:** `backend/app/api/v1/conversations.py:40-41`, `backend/app/api/v1/long_term_memory.py:73-90`
- **Risk of fix:** LOW
- **Details:**
  - **Conversations:** `limit` and `offset` are bare `int` parameters with no `Field(ge=0, le=...)` constraints. A client could pass `limit=999999` or `offset=-1`.
  - **Long-term memory:** The `GET /long-term-memory` endpoint has NO `limit`/`offset` parameters at all. It returns all memories for a user (grouped by category). For users with many memories, this could return unbounded data.
- **Change:** Add Pydantic validation or `Query(...)` constraints: `limit: int = Query(default=50, ge=1, le=200)`, `offset: int = Query(default=0, ge=0)`. For long-term memory, add optional `limit`/`offset` with sensible defaults.

---

## M-Q7: Race conditions in async code
- **Still an issue:** NO (misidentified)
- **File:** `backend/app/agents/background.py`
- **Risk of fix:** N/A
- **Details:** The module uses global dicts `_active_runs` and `_event_queues` modified by async coroutines. However, asyncio is single-threaded — there are no true race conditions between coroutines since only one runs at a time and dict operations are atomic in CPython. The only risk is a memory leak: `_event_queues` is never cleaned up after a run completes (queues accumulate). This is a resource leak, not a race condition.

---

## M-CL3: Redundant auth/security.py
- **Still an issue:** YES
- **File:** `backend/app/auth/security.py:1-3`
- **Risk of fix:** LOW
- **Details:** `auth/security.py` is 3 lines: it re-exports `hash_password`, `verify_password`, `validate_password_strength` from `core/security.py`. No additional logic. Creates an unnecessary indirection layer.
- **Change:** Update all imports from `backend.app.auth.security` to `backend.app.core.security`. Delete `auth/security.py`.

---

## M-CL5: Unused UI components
- **Still an issue:** YES
- **Files:** `frontend/src/shared/ui/Tooltip.tsx`, `frontend/src/shared/ui/StaggerChildren.tsx`, `frontend/src/shared/ui/Steps.tsx`
- **Risk of fix:** LOW
- **Details:**
  - `Tooltip.tsx`: Not imported anywhere in the codebase (grep found 0 imports).
  - `StaggerChildren.tsx`: Not imported anywhere (grep found 0 imports).
  - `Steps.tsx`: Not imported anywhere (grep found 0 imports).
  - All three are dead code. They're well-written components but unused.
- **Change:** Delete the three files. If they're planned for future use, document them or move to a `_future/` directory.

---

## M-CL8: WorkloadRecommendations unused
- **Still an issue:** NO
- **Files:** `frontend/app/models/WorkloadRecommendations.tsx`, imported by `frontend/app/models/ModelsPage.tsx:21` and `frontend/app/models/components/WorkloadColumns.tsx:4`
- **Risk of fix:** N/A
- **Details:** `WorkloadRecommendations` is defined and actively imported by `ModelsPage.tsx` (as `WorkloadRecs`) and `WorkloadColumns.tsx`. It is used. This was a false positive.

---

## Summary

| ID | Still Issue? | Risk | Action |
|----|-------------|------|--------|
| M-S1 | YES | LOW | Remove vault from CSRF exempt list |
| M-S3 | NO | — | Already fixed |
| M-S5 | YES | LOW | Add per-user WS connection limits |
| M-S6 | YES | MEDIUM | Make CORS origins env-configurable |
| M-S8 | YES | LOW | Add validate_storage_path call |
| M-C1 | NO | — | Already fixed |
| M-C4 | YES | LOW | Align backend schema to return list |
| M-D1 | YES | MEDIUM | Add unique constraint on code_chunks |
| M-D2 | YES | HIGH | Systemic datetime consistency fix |
| M-D4 | YES | LOW | Add migration for ix_users_deleted_at |
| M-Q3 | YES | LOW | Add limit/offset validation |
| M-Q7 | NO | — | Not a race condition (asyncio single-threaded) |
| M-CL3 | YES | LOW | Remove redundant re-export file |
| M-CL5 | YES | LOW | Delete unused UI components |
| M-CL8 | NO | — | False positive, component is used |
