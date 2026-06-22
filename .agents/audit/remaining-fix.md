# Remaining Fixes & Recommendations

> Last updated: 2026-06-22
> Purpose: Single source of truth for all pending work across Cortex

---

## P0/P1 Critical — Must Fix

| # | Issue | File(s) | What to do |
|---|-------|---------|------------|
| 1 | Agent self-approval partially bypassable | `agents/executor.py:52-58` | Need crypto-signed human confirmation, not just LLM tool-call blocking |
| 2 | In-memory token stores not process-safe (multi-worker) | `core/security.py:96-137` | Document limitation or remove in-memory fallback |
| 3 | `SyncStatusResponse` fields always zero/None | `api/v1/sync.py:418-426` | `pending_changes` and `indexed_files` hardcoded to 0 — need real data from SyncState |
| 4 | Repository registration no path restrictions | `api/v1/repository.py:85-104` | Validate repo paths within user's storage root |
| 5 | `/metrics` unauthenticated + rate-limit exempt | `api/metrics.py:32-69` | Require auth or restrict to admin |
| 6 | `run.error` stores internal exception messages | `agents/run_manager.py:136` | Sanitize `step.observation` — don't store raw exceptions |

---

## Security — Pending

| # | Issue | Severity | File(s) | What to do |
|---|-------|----------|---------|------------|
| 1 | WebSocket tokens in URL (logs, browser history) | HIGH | `api/ws.py:21`, `api/v1/ws_system.py:61` | Move to secure cookie or WS handshake header |
| 2 | Password validation weak | MEDIUM | `core/security.py:30-35` | Require uppercase, special char, common-password check |
| 3 | Vault password re-encryption not atomic | MEDIUM | `services/vault_service.py:560-625` | Add backup/temp files + rollback |
| 4 | Vault password cached plaintext in memory | MEDIUM | `services/vault_service.py:40-87` | Document limitation or use bytearray more carefully |
| 5 | `SECRET_KEY` rotation mechanism missing | LOW | `core/config.py` | Implement key rotation support |
| 6 | Redis no password in docker-compose | LOW | `docker-compose.yml:20-30` | Add Redis password |
| 7 | Repositories with `user_id=NULL` visible to all | LOW | `api/v1/repository.py:67-69` | Filter to owner-only |
| 8 | CSP dev mode allows `ws://localhost:*` | LOW | `core/middleware.py:11-18` | Restrict in production |
| 9 | No `Cache-Control: no-store` on auth responses | LOW | `core/middleware.py` | Add header |
| 10 | No `Permissions-Policy` header | LOW | `core/middleware.py` | Add header |
| 11 | Deprecated `x-xss-protection` header | LOW | `core/middleware.py:33` | Remove |
| 12 | Hardcoded DB credentials as defaults | LOW | `core/config.py:14` | Remove from source |

---

## DB — Pending

| # | Issue | Severity | File(s) | What to do |
|---|-------|----------|---------|------------|
| 1 | Missing `server_default` on 15+ NOT NULL timestamps | HIGH | `migrations/b00000000000_baseline.py` | Add `server_default=sa.func.now()` |
| 2 | Raw SQL for CHECK constraints (non-portable) | HIGH | `migrations/b00000000000_baseline.py:77-79` | Use `op.create_check_constraint()` |
| 3 | Raw SQL for GIN indexes (non-portable) | HIGH | `migrations/b00000000000_baseline.py:866-873` | Use proper Alembic API |
| 4 | Downgrade missing `if_exists` guards | HIGH | `migrations/b00000000000_baseline.py:882-916` | Add `if_exists=True` |
| 5 | FK columns missing indexes (3 tables) | HIGH | `migrations/b00000000000_baseline.py` | `model_variants.provider_id`, `provider_model_id`, `sync_states.repo_id` |
| 6 | `model_variants.model_catalog_id` nullable mismatch | MEDIUM | `migrations/b00000000000_baseline.py:517` | Add `nullable=False` |
| 7 | `agents.name` missing unique constraint | MEDIUM | `migrations/b00000000000_baseline.py:257` | Add `unique=True` |
| 8 | `CodeChunk` missing unique constraint | MEDIUM | `models/repo_index.py:32-48` | Add `UniqueConstraint` + migration |
| 9 | `models/__init__.py` exports only 13 of 28 models | MEDIUM | `models/__init__.py:41-55` | Export all model classes |
| 10 | `knowledge_entries` missing unique constraint | MEDIUM | `migrations/b00000000000_baseline.py:94-115` | Add `UniqueConstraint("user_id", "source_path", "category")` |
| 11 | `EmbeddingCache` no TTL enforcement | MEDIUM | `models/embedding_cache.py:26` | Add scheduled cleanup job |
| 12 | `TIMESTAMP` vs `TIMESTAMPTZ` inconsistency | LOW | All timestamp columns | Standardize to `TIMESTAMPTZ` |
| 13 | `model_variants` duplicate columns | LOW | `migrations/b00000000000_baseline.py:514-555` | Schema debt — consolidate |
| 14 | Engine pool settings too conservative | LOW | `db/bootstrap.py:52-59` | Consider `pool_size=10` for production |

---

## Quality — Pending

| # | Issue | Severity | File(s) | What to do |
|---|-------|----------|---------|------------|
| 1 | Empty `LLMHealthResponse`/`LLMMetricsResponse` stubs | P2 | `schemas/model.py:108-113` | Populate with actual fields |
| 2 | 7 endpoints return raw dicts, no typed responses | P2 | `api/v1/models.py` | Add `response_model=` to health, metrics, inference config |
| 3 | `models.py` is 927 lines | P2 | `api/v1/models.py` | Split into sub-routers (catalog, downloads, settings) |
| 4 | DateTime tz-aware/naive inconsistency | P2 | Multiple models | Systemic fix — all `TIMESTAMPTZ` or all naive UTC |
| 5 | Default value mechanism inconsistency | P2 | Multiple models | Audit all models, ensure `server_default` |
| 6 | `parameter_count` type mismatch (str vs float) | P2 | `schemas/model.py` (6 classes) | Align to float |
| 7 | `LLMManager.chat()` creates raw `SessionLocal()` | P2 | `services/llm/manager.py:104-118` | Accept session as parameter |
| 8 | Lazy singletons without thread safety | P2 | `embedding_service.py:203-210`, `file_watcher_v2.py:141-148` | Use `@lru_cache` or add locks |
| 9 | Missing circuit breaker for external services | P2 | `embedding_service.py`, `hybrid_retrieval.py` | Add circuit breaker for Ollama/Qdrant |
| 10 | Deep health check only checks DB | P2 | `api/v1/health.py:24-33` | Add Redis, Ollama, Qdrant checks |
| 11 | `SECRET_KEY` defaults to empty string | P2 | `core/config.py:10` | Generate random key on startup if none provided |
| 12 | `AgentFeedbackCreateResponse.feedback` typed as `dict` | P3 | `schemas/agent.py:96` | Use typed schema |
| 13 | Hardcoded English GIN index config | P3 | `migrations/b00000000000_baseline.py:866-873` | Use `simple` config |
| 14 | `IndexedFile.is_stale()` uses `os.stat()` in model | P3 | `models/file_index.py:34-45` | Move to service layer |

---

## UI/UX — Pending

### HIGH Priority

| # | Issue | File(s) | What to do |
|---|-------|---------|------------|
| 1 | WebSocket `?token=` missing — always receives None | `useSystemWebSocket.ts:82`, `ws_system.py:61` | Append `?token=` to WS URL |
| 2 | WebSocket missing processes data | `ws_system.py:29-41` | Add `processes` to `collect_metrics()` |
| 3 | No VRAM monitoring on dashboard | `app/app/page.tsx`, `system_info.py` | Add 4th MetricRing for VRAM |
| 4 | AgentChat uses polling, not SSE streaming | `agents/AgentChat.tsx` | Switch to SSE endpoint `/agents/runs/{run_id}/stream` |
| 5 | No LLM/model settings UI (backend exists) | `app/settings/page.tsx` | Build settings form for `inference_backend`, `huggingface_token`, etc. |

### MEDIUM Priority

| # | Issue | File(s) | What to do |
|---|-------|---------|------------|
| 6 | Activity tab shows backend logs, not user activity | `app/app/page.tsx:186-211` | Create user activity event system |
| 7 | Insights tab is just 4 static cards | `app/app/page.tsx:266-313` | Add usage trends, health summary |
| 8 | Memory page is 1310+ line monolith | `app/memory/page.tsx` | Extract graph view, sync management, learning view |
| 9 | MemoryEditor category free-text but backend validates | `MemoryEditor.tsx:110-116` | Replace with dropdown of 8 valid categories |
| 10 | Search orphaned components not wired | `app/search/SearchFilters.tsx`, `SearchResults.tsx`, `GraphView.tsx` | Wire into `page.tsx` or delete |
| 11 | No pagination in search results | `app/search/page.tsx` | Add "Load more" using `next_cursor`/`has_more` |
| 12 | No model/tool selection during agent creation | `agents/page.tsx:261-319` | Add model dropdown + tools selector |
| 13 | No feedback UI for agent runs | `agents/page.tsx` | Add thumbs up/down on responses |
| 14 | No conversation renaming | `chat/page.tsx` | Add inline edit on title |
| 15 | No stop/cancel button for streaming | `chat/page.tsx` | Add abort controller support |
| 16 | Model detail benchmarks hardcoded | `ModelDetailPage.tsx:318-323` | Use `model.benchmarks` from backend |
| 17 | "Add to Compare" button non-functional | `ModelDetailPage.tsx:388-391` | Wire to `/models/compare` endpoint |
| 18 | Catalog "Fit" column always shows "—" | `CatalogTable.tsx:132` | Pass VRAM compatibility data |
| 19 | HardwareBar only static snapshot | `HardwareBar.tsx` | Add WebSocket-based live telemetry |
| 20 | No sync status indicator on memory page | `app/memory/page.tsx` | Add sync badge in header |

### LOW Priority

| # | Issue | File(s) | What to do |
|---|-------|---------|------------|
| 21 | Chat conversation list only title, no preview | `chat/page.tsx` | Add last message preview |
| 22 | Accent color saved but not applied globally | `app/settings/page.tsx:143-202` | Wire to CSS variables |
| 23 | Notifications button shows "coming soon" | `DashboardShell.tsx:462` | Build notification panel |
| 24 | Delete uses `window.confirm()` | `MemoryDetail.tsx:25` | Replace with design system modal |
| 25 | No tests for Landing/Downloads pages | `app/page.tsx`, `app/downloads/` | Add test coverage |
| 26 | Error boundaries duplicated (3 files) | `error.tsx` | Extract to shared component |
| 27 | Search page missing auth redirect | `app/search/page.tsx` | Add `useAuth()` pattern |

---

## Frontend-Backend Contract Mismatches

| # | Issue | Frontend Expects | Backend Returns | Severity |
|---|-------|-----------------|-----------------|----------|
| 1 | `recommended()` response shape | `{hardware, recommended: ModelInfo[]}` | `{hardware, workloads: {...}}` | HIGH |
| 2 | `installed()` item shape | `ModelCatalogEntry` (12 fields) | `InstalledModel` (6 fields) | HIGH |
| 3 | `downloadHistory` item shape | Has `speed_bytes_sec`/`eta_seconds` | Returns `completed_at`/`created_at` | HIGH |
| 4 | `compare()` extra field | No `models` field | Returns `models` array | HIGH |
| 5 | `search()` result shape | Full `ModelInfo` | Simpler 10-field shape | HIGH |
| 6 | `usageStats` param ignored | Sends `?model_id=X` | Ignores the param | HIGH |
| 7 | Long-term memory list shape | `{grouped: {...}}` | `{memories: [...]}` when filtered | MEDIUM |
| 8 | Chat timestamp drift | Client `new Date()` | Server `func.now()` | LOW |
| 9 | Repo graph routes | `/api/v1/repos/{id}/graph` | No backend route exists | LOW |

---

## Architecture Cleanup

| # | Task | Priority | Files |
|---|------|----------|-------|
| 1 | Delete `file_watcher.py` (dead code, name-shadowing) | HIGH | `services/file_watcher.py` |
| 2 | Delete `threaded_scanner.py` (dead code) | HIGH | `services/threaded_scanner.py` |
| 3 | Delete `search_clustering.py` (dead code) | HIGH | `services/search_clustering.py` |
| 4 | Remove `embed_with_cache` dead method | HIGH | `services/embedding_service.py` |
| 5 | Fix `sync.py` session pattern | HIGH | `api/v1/sync.py` |
| 6 | Clean up sync job stubs | HIGH | `api/v1/sync.py:336-337` |
| 7 | Extract `models.py` helper functions to service | MEDIUM | `api/v1/models.py` |
| 8 | Create `conversationApi` client | LOW | `frontend/src/shared/api/` |
| 9 | Consolidate `cortexApi.ts` into domain modules | LOW | `frontend/src/shared/api/` |

---

## Ollama Integration — Remaining

| # | Item | What to do |
|---|------|------------|
| 1 | `last_used` / `usage_count` tracking | Add from Ollama or usage tracker |
| 2 | Frontend periodic polling for installed models | Add WS subscription or polling |

---

## Roadmap (Execution Order)

### Phase 1: Critical Security + Data Integrity
- P0/P1 issues (6 items above)
- Security pending items (12 items above)

### Phase 2: DB Cleanup
- Migration fixes (5 HIGH items)
- Schema standardization (9 MEDIUM/LOW items)

### Phase 3: Live Data
- WebSocket auth fix (#1 UI HIGH)
- VRAM monitoring (#3 UI HIGH)
- Processes data in WS (#2 UI HIGH)

### Phase 4: Search & Agents
- SSE streaming for agents (#4 UI HIGH)
- Search pagination + component wiring

### Phase 5: Chat Redesign
- Complete UI redesign
- Conversation renaming, stop/cancel, message actions

### Phase 6: Models & Settings
- Settings UI (#5 UI HIGH)
- Contract mismatches (6 HIGH items)
- Compare button, benchmarks

### Phase 7: Dashboard & Polish
- Activity events, insights
- Error boundary extraction, tests

### Phase 8: Architecture Cleanup
- Dead code deletion (4 items)
- `models.py` split
- API module consolidation
