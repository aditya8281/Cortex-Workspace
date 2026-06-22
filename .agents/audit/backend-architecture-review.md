# Cortex Backend Architecture Review & Execution Roadmap

Generated: 2026-06-22

---

## Part 1: Validated Findings

Every finding from the backend audit report has been validated against the actual codebase. Each is classified as confirmed, modified, or rejected.

### 1.1 Confirmed Findings

#### F1: `sync/jobs` endpoints are stubs returning empty/404

**Root problem:** The old `FileWatcher` (v1, poll-based) had in-memory job tracking with `SyncJob` dataclasses. When v2 replaced it with watchdog-based watching, job tracking was dropped but the API endpoints were kept as stubs.

**Impact:** Frontend polls `GET /sync/jobs` every 5 seconds (memory/page.tsx:182, SyncStatus.tsx:464) for jobs that never arrive. Dead code paths exist for displaying job progress that can never trigger. The `initial_scan_status` display in the sync modal reads data the API never returns.

**Severity:** Low — The actual sync works fine (files get watched and indexed). The stubs create misleading dead code but don't break functionality.

**Verdict:** CONFIRMED — Fix or remove, don't leave as stubs.

---

#### F2: Empty `LLMHealthResponse` and `LLMMetricsResponse` stubs

**Root problem:** Author planned to type health/metrics responses but never completed the work.

**Impact:** Both classes are dead code — never imported anywhere. The endpoints use `response_model=dict` and return raw dicts. OpenAPI schema shows `response: {}` for these endpoints. No runtime validation occurs.

**Severity:** Low — Dead code, but the untyped dict returns are a mild concern for API contract quality.

**Verdict:** CONFIRMED — Replace with real typed models or remove the stubs.

---

#### F3: `file_watcher.py` is dead code (289 lines)

**Root problem:** Legacy file from before the v2 watchdog rewrite. Never cleaned up.

**Impact:** Zero imports anywhere in production code or tests. Defines an in-memory `SyncJob` dataclass that name-shadows the real SQLAlchemy `SyncJob` model in `model_catalog.py:255`. If anyone accidentally imports from this file, they get the wrong type.

**Severity:** Low — Dead code with a name-shadowing risk.

**Verdict:** CONFIRMED — Delete the file.

---

#### F4: `threaded_scanner.py` is dead code (234 lines)

**Root problem:** Experimental multi-threaded scanner inspired by sist2's fork-based approach. Never integrated into the scanning pipeline.

**Impact:** Zero imports anywhere in the codebase. The actual scanning is done by `repo_scanner.py` which doesn't use this utility.

**Severity:** Low — Dead code.

**Verdict:** CONFIRMED — Delete the file.

---

#### F5: `models.py` is 927 lines with 25 endpoints

**Root problem:** The models domain is the largest in the backend. The file mixes routing, business logic (inline dict construction), and utility functions (145 lines of helpers at lines 790-927).

**Impact:** The file is not well-organized. The length is driven by:
- ~200 lines of inline dict construction instead of delegating to schemas
- ~145 lines of private helper functions unrelated to routing
- ~80 lines of service calls with inline result mapping

However, the endpoints do group into 7 logical clusters (Catalog, Downloads, Sync, Settings, Updates, Health/Metrics, Usage). Each cluster could own its own sub-router.

**Severity:** Medium — Maintainability concern, not a correctness issue.

**Verdict:** CONFIRMED — Split into sub-routers and extract helpers to service layer.

---

#### F6: `SessionLocal()` usage in sync.py (3 endpoints)

**Root problem:** The sync endpoints use `Depends(get_current_user)` for auth but never accept `db: Session = Depends(get_db)`. Since `get_current_user` only returns a `User` object (not the session), the handler creates its own session manually.

**Impact:** Two sessions open simultaneously for every sync request. With `pool_size=5, max_overflow=10`, this halves effective concurrency from ~15 to ~7 for sync requests. All sessions are properly closed (no leaks), so this is a resource waste, not a correctness issue.

**Severity:** Low-Medium — Resource waste under load, but sync is not a high-throughput endpoint.

**Verdict:** CONFIRMED — Add `db: Session = Depends(get_db)` parameter, remove manual `SessionLocal()` calls.

---

#### F7: `SessionLocal()` in profile.py `_photo_dir` helper

**Root problem:** The `_photo_dir` function is a plain helper, not a FastAPI dependency or route handler. It cannot use `Depends(get_db)`.

**Impact:** This is actually the correct pattern for non-DI contexts. The session is properly closed with double try/finally.

**Severity:** None — This is not a problem.

**Verdict:** REJECTED — The audit incorrectly flagged this. Manual `SessionLocal()` is correct for plain functions outside DI.

---

#### F8: Embedding mock fallback has no production guard

**Root problem:** The 3-tier fallback (ONNX → Ollama → Mock) always succeeds, even in production. The mock silently poisons the vector database with garbage embeddings.

**Impact:** A user doing a full sync in production with mock embeddings would corrupt their search index with no visible signal. Once mock embeddings are stored, they must be purged and re-indexed. The mock is also exposed as a selectable model in the UI dropdown alongside real models.

**Severity:** Medium — Development convenience vs. production safety tension.

**Verdict:** CONFIRMED — Add hard-fail mode in production or at minimum an API health flag.

---

#### F9: 7 endpoints return raw dicts instead of typed responses

**Root problem:** Endpoints for hardware, health, metrics, inference-config, download queue, download history, and recommended models have no properly typed response model.

**Impact:** OpenAPI schema is degraded. No runtime validation. Frontend must guess response shapes.

**Severity:** Medium — API contract quality issue.

**Verdict:** CONFIRMED — Add proper Pydantic response models.

---

#### F10: `search_clustering.py` is dead code (44 lines)

**Root problem:** Never imported anywhere in production code or tests.

**Severity:** Low — Dead code.

**Verdict:** CONFIRMED — Delete or integrate.

---

#### F11: `model_detail_scraper.py` only used in tests (264 lines)

**Root problem:** Only imported by `test_model_detail_scraper.py`. Never used in production.

**Severity:** Low — Test-only code that could be test fixtures.

**Verdict:** CONFIRMED — Move to test fixtures or delete.

---

#### F12: `seed_data.py` only used in tests (295 lines)

**Root problem:** Only imported by `test_seed_data.py`. Never called during app startup or migrations.

**Severity:** Low — Test-only code.

**Verdict:** CONFIRMED — Move to test fixtures or delete.

---

#### F13: `embed_with_cache` method is dead code

**Root problem:** Defined in `embedding_service.py:169` but never called anywhere.

**Severity:** Low — Dead code.

**Verdict:** CONFIRMED — Remove the method.

---

### 1.2 Modified Findings

#### M1: Frontend-backend alignment gaps need clarification

The audit agent's analysis contained errors. After validation:

**Incorrectly flagged as "no frontend consumer":**
- **Conversations endpoints** — The chat page (`chat/page.tsx`) calls these directly via `api.get/post/delete`, not through the centralized cortexApi client. They ARE consumed.
- **Long-term memory endpoints** — The memory page (`memory/page.tsx:150-177`) calls these directly via `api.get/post/delete`. They ARE consumed.

**Actually missing frontend consumer:**
- **Knowledge endpoints** (`/knowledge/health`, `/knowledge/stats`, `/knowledge/retrieval-metrics`) — No frontend code calls these. The `knowledgeApi.health()` and `knowledgeApi.stats()` functions exist but are never called from any component.
- **Agent metrics** (`/agents/metrics`) — No frontend consumer.
- **Agent SSE streaming** (`/agents/runs/{id}/stream`) — The frontend polls `getRunStatus()` instead of subscribing to the stream.

**Phantom parameters (frontend sends, backend ignores):**
- `node_type`, `language` in search API calls
- `model_id` in usage stats API call

---

#### M2: Notification gap is real but scoped

The backend has full notification CRUD (list, mark read, mark all read, delete). The frontend has API client functions but only uses `apiListNotifications` for unread badge count. No UI exists to:
- Display the full notification list/panel
- Mark individual or all notifications as read
- Delete notifications

**Modified recommendation:** This is a genuine gap but not critical. The notification system is infrastructure for future features (download complete, sync finished, agent run complete). Building the UI now is premature until there are actual notification sources.

---

#### M3: Sync status type mismatch is real

The frontend `WatchedPath` type expects 6 fields (`path`, `repo_id`, `embedding_model`, `sync_enabled`, `initial_scan_job_id`, `initial_scan_status`) but the backend only returns 2 (`path`, `status`).

**Modified recommendation:** This is a real type mismatch that causes undefined values at runtime. The backend should return the full watched path data, or the frontend type should be simplified to match what the backend actually provides.

---

## Part 2: Rejected Findings

### R1: Implement `ServiceProtocol` for Tauri IPC

**Audit recommendation:** Complete the Tauri IPC abstraction layer by implementing `ServiceProtocol` across all services.

**Why rejected:**
- `ServiceProtocol` is an abstract base class with `execute(action, params)` and `health_check()`. No service currently implements it.
- Tauri is not yet in active development. The project is pre-production with no desktop users.
- Implementing this now would be speculative architecture — designing for a Tauri integration that may never materialize in the current form.
- When Tauri IS needed, the actual IPC requirements will be known and can drive the interface design properly.
- Premature abstraction creates maintenance burden without usage.

**Verdict:** REJECT — Defer until Tauri integration is actively planned.

---

### R2: Remove embedding mock fallback entirely

**Audit recommendation:** Per architecture decision, fail explicitly in production if no real embedding model available.

**Why modified to partial rejection:**
- The mock is genuinely useful for development, testing, and UI development without GPU.
- A hard-fail in production is correct, but removing the mock entirely would break the development workflow.
- Better approach: Add a `production` flag that disables mock in non-development environments. Keep mock available for `ENVIRONMENT=development`.

**Verdict:** PARTIALLY REJECT — Don't remove mock; add environment-based guard.

---

### R3: `LLMManager` thread safety for metrics

**Audit recommendation:** The `LLMManager` accumulates metrics in plain int fields that are not thread-safe under concurrent async coroutines.

**Why rejected:**
- FastAPI runs on a single-threaded event loop (uvicorn with asyncio). Async coroutines on the same event loop do not execute concurrently — they cooperative multitask. Plain `int` field mutations with `+=` are safe under single-threaded asyncio.
- This would only be a problem with multi-threaded workers (e.g., `multiprocessing`), which Cortex doesn't use.
- Adding locks would add complexity without benefit.

**Verdict:** REJECT — Not a real problem under asyncio's execution model.

---

## Part 3: Additional Findings

### A1: `LLMManager.chat()` and `chat_stream()` create raw DB sessions

**Root problem:** The LLM manager creates `SessionLocal()` inside method bodies (lines 104-116, 173-186) to persist token usage, bypassing FastAPI's dependency injection.

**Impact:** Same double-session issue as F6, but in a more critical path (every chat message). The sessions are properly closed but waste connection pool slots.

**Severity:** Medium — Every chat request wastes a connection.

**Recommendation:** Accept the DB session as a parameter instead of creating it internally.

---

### A2: `search_clustering.py` is dead code (44 lines)

**Root problem:** Never imported anywhere. Likely planned for result clustering but never integrated.

**Severity:** Low.

**Recommendation:** Delete the file.

---

### A3: Frontend types defined but never consumed

**Root problem:** `LongTermMemory`, `MemoryStats`, `Conversation`, `ConversationMessage`, `ConversationDetail` types are defined in `types.ts` but never used in API calls or components (the actual usage is inline in page components).

**Impact:** Dead type definitions create confusion about what's actually used.

**Severity:** Low.

**Recommendation:** Remove unused type exports or consolidate to where they're actually used.

---

### A4: `SyncState` model fields never updated

**Root problem:** `SyncState` has `last_sync_at` and `files_changed` fields that are never written to by any code. The model exists but its richer fields are never populated.

**Impact:** The data model promises features (sync timing, change tracking) that don't exist.

**Severity:** Low — Schema-only issue.

**Recommendation:** Either populate these fields in the sync workflow or remove them.

---

### A5: Models route file mixes business logic with routing

**Root problem:** The 927-line `models.py` contains ~200 lines of inline dict construction that duplicates schema shapes, ~145 lines of private utility functions, and ~80 lines of manual result mapping.

**Impact:** The route handlers are doing work that should be in services or schemas. This makes the handlers harder to test and the business logic harder to reuse.

**Severity:** Medium.

**Recommendation:** Extract helper functions to a service module, use Pydantic response models instead of inline dict construction.

---

## Part 4: Prioritized Execution Roadmap

### Tier 1: Fix Broken Things + Remove Dead Code (1-2 days)

| # | Item | Root Problem | Solution | Effort | Risk |
|---|------|-------------|----------|--------|------|
| 1.1 | Delete `file_watcher.py` | Dead code with name-shadowing risk | Delete the file | 5 min | None |
| 1.2 | Delete `threaded_scanner.py` | Dead code | Delete the file | 5 min | None |
| 1.3 | Delete `search_clustering.py` | Dead code | Delete the file | 5 min | None |
| 1.4 | Remove `embed_with_cache` dead method | Dead code | Remove method | 5 min | None |
| 1.5 | Fix `sync.py` session pattern | Double-session resource waste | Add `Depends(get_db)`, remove `SessionLocal()` | 30 min | Low |
| 1.6 | Clean up sync job stubs | Dead frontend polling code | Either remove stub endpoints and dead frontend code, or implement lightweight job tracking | 2-4 hrs | Low |
| 1.7 | Fix sync status type mismatch | Frontend expects 6 fields, backend returns 2 | Align backend response with frontend type or vice versa | 1 hr | Low |

**Total: ~4-6 hours**

---

### Tier 2: API Contract Quality + Type Safety (2-3 days)

| # | Item | Root Problem | Solution | Effort | Risk |
|---|------|-------------|----------|--------|------|
| 2.1 | Replace empty LLM health/metrics stubs | Dead code, untyped dict returns | Create real Pydantic models for health and metrics responses | 2 hrs | Low |
| 2.2 | Add typed response models to 7 untyped endpoints | Raw dict returns degrade OpenAPI schema | Create Pydantic response models for hardware, health, metrics, inference-config, download queue, download history, recommended | 4 hrs | Low |
| 2.3 | Fix `response_model=None` on recommended endpoint | Typed objects returned but schema not exposed | Add proper response_model | 15 min | None |
| 2.4 | Remove phantom frontend parameters | Frontend sends parameters backend ignores | Remove `node_type`, `language`, `model_id` from frontend calls | 30 min | None |
| 2.5 | Move `models.py` helper functions to service layer | 145 lines of utilities mixed with routing | Extract to `backend/app/services/model_helpers.py` | 2 hrs | Low |
| 2.6 | Move `model_detail_scraper.py` to test fixtures | Test-only code in production | Move or delete | 30 min | None |
| 2.7 | Move `seed_data.py` to test fixtures | Test-only code in production | Move or delete | 30 min | None |

**Total: ~10-12 hours**

---

### Tier 3: Frontend-Backend Alignment (2-3 days)

| # | Item | Root Problem | Solution | Effort | Risk |
|---|------|-------------|----------|--------|------|
| 3.1 | Add conversation last_message to list endpoint | Chat sidebar shows titles only, no preview | Add `last_message_content` and `last_message_at` to `ConversationResponse`, modify list query to JOIN last message | 3 hrs | Low |
| 3.2 | Add notification panel UI | Backend CRUD exists, frontend has no UI | Create `NotificationPanel` dropdown in DashboardShell | 4 hrs | Low |
| 3.3 | Wire knowledge API to frontend | Backend health/stats/metrics exist, no UI | Add knowledge health display to dashboard or settings | 2 hrs | Low |
| 3.4 | Fix accent color application | Settings saves preference, doesn't apply it | Create ThemeProvider, add CSS variables, update Tailwind config | 2 hrs | Low |
| 3.5 | Wire agent SSE streaming | Backend supports SSE, frontend polls instead | Subscribe to `/agents/runs/{id}/stream` in agent chat | 4 hrs | Medium |

**Total: ~15-17 hours**

---

### Tier 4: Architecture Improvements (3-5 days)

| # | Item | Root Problem | Solution | Effort | Risk |
|---|------|-------------|----------|--------|------|
| 4.1 | Fix LLMManager DB session pattern | `chat()` creates raw sessions inside method | Accept session as parameter | 3 hrs | Low |
| 4.2 | Add embedding mock production guard | Mock silently corrupts vector store in production | Add `ENVIRONMENT` check, hard-fail when mock is used in production, label mock as "dev only" in UI | 2 hrs | Low |
| 4.3 | Populate `SyncState` fields | `last_sync_at` and `files_changed` never written | Add updates in sync workflow | 1 hr | Low |
| 4.4 | Split `models.py` into sub-routers | 927 lines mixing routing and business logic | Create `models_catalog.py`, `models_downloads.py`, `models_settings.py` sub-routers | 4 hrs | Medium |
| 4.5 | Remove unused frontend type exports | Dead types create confusion | Clean up `types.ts` | 30 min | None |
| 4.6 | Remove phantom search parameters | Frontend sends unused parameters | Clean up search API calls | 30 min | None |

**Total: ~11-13 hours**

---

### Tier 5: Observability & Monitoring (3-5 days)

| # | Item | Root Problem | Solution | Effort | Risk |
|---|------|-------------|----------|--------|------|
| 5.1 | Build notification center UI | Backend exists, no frontend | NotificationPanel with list, mark read, delete | 4 hrs | Low |
| 5.2 | Build background task visibility | Tasks run silently with no progress | Task center showing active/completed/failed tasks | 8 hrs | Medium |
| 5.3 | Build knowledge health dashboard | Backend metrics exist, no UI | Display retrieval metrics, knowledge health on dashboard | 4 hrs | Low |
| 5.4 | Build agent activity center | Agent runs have no centralized view | Aggregated run view across all agents | 6 hrs | Medium |

**Total: ~22-24 hours**

---

### Tier 6: Tauri Readiness (Defer)

| # | Item | Root Problem | Solution | Effort | Risk |
|---|------|-------------|----------|--------|------|
| 6.1 | ServiceProtocol implementations | Tauri IPC abstraction layer | Defer until Tauri integration is actively planned | N/A | N/A |
| 6.2 | Rust crate extraction | Performance-critical paths | Defer until Tauri integration is actively planned | N/A | N/A |

**Verdict:** Defer all Tauri-related work until the desktop integration is actively planned with known requirements.

---

## Part 5: Frontend-Backend Integration Audit

### Features with Backend Support but No Frontend Experience

| Backend Feature | Status | Frontend Gap | Priority |
|----------------|--------|-------------|----------|
| Notification CRUD | ✅ 4 endpoints | No UI to view/manage notifications | Medium |
| Knowledge health/stats | ✅ 3 endpoints | No UI consumer | Low |
| Retrieval metrics | ✅ 1 endpoint | No frontend API client or UI | Low |
| Agent metrics | ✅ 1 endpoint | No frontend consumer | Low |
| Agent SSE streaming | ✅ 1 endpoint | Frontend polls instead of subscribing | Medium |
| Conversation previews | ⚠️ Schema missing field | Chat sidebar shows titles only | High |
| Accent color preference | ✅ Saved to DB | Not applied to CSS variables | High |
| Sync job tracking | ⚠️ Stub endpoints | Frontend polls dead endpoints | Medium |

### Features with Frontend Expectations but Incomplete Backend

| Frontend Feature | Backend Gap | Priority |
|-----------------|-------------|----------|
| Sync watched_paths type | Backend returns 2 of 6 expected fields | Medium |
| Search pagination | Backend supports cursor pagination, frontend doesn't use it | Low |
| Usage stats per model | Frontend sends `model_id` param, backend ignores it | Low |

---

## Part 6: What NOT to Do

1. **Do not implement ServiceProtocol across services** — Premature abstraction for unproven Tauri requirements
2. **Do not remove embedding mock entirely** — Useful for development; add environment guard instead
3. **Do not add locks to LLMManager metrics** — asyncio is single-threaded; locks add complexity without benefit
4. **Do not split models.py for line count alone** — Split only if the logical clusters genuinely benefit from separate files
5. **Do not build notification UI before there are notification sources** — The infrastructure is ready; build the UI when there are actual notifications to show
6. **Do not refactor session patterns in profile.py** — The `_photo_dir` helper correctly uses `SessionLocal()` because it's outside DI

---

## Part 7: Summary

| Category | Count | Total Effort |
|----------|-------|-------------|
| Tier 1: Fix broken things + remove dead code | 7 items | ~4-6 hours |
| Tier 2: API contract quality + type safety | 7 items | ~10-12 hours |
| Tier 3: Frontend-backend alignment | 5 items | ~15-17 hours |
| Tier 4: Architecture improvements | 6 items | ~11-13 hours |
| Tier 5: Observability & monitoring | 4 items | ~22-24 hours |
| Tier 6: Tauri readiness | 2 items | Defer |
| **Total** | **31 items** | **~62-72 hours** |

**Optimal execution order:** Tier 1 → Tier 2 → Tier 3 → Tier 4 → Tier 5 → Tier 6 (defer)

**Key principles:**
- Fix broken things first (dead code, type mismatches, session patterns)
- Improve API contracts before building new UI
- Align frontend and backend before adding new features
- Defer Tauri work until requirements are known
- Don't build infrastructure before there are consumers
