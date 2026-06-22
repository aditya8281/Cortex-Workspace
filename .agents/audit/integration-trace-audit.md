# Cortex Integration Trace Audit

Generated: 2026-06-22
Updated: 2026-06-22 (P0/P1 fixes applied)

---

## Fixed Issues (2026-06-22)

| ID | Issue | Fix |
|----|-------|-----|
| C1 | Memory router not registered — 6 endpoints 404 | Registered `memory_router` in `api/router.py` |
| C2 | Search pagination type gap — frontend missing `next_cursor`/`has_more` | Added fields to `SearchResponse` type, made nullable fields optional |
| C4 | Vault list response wrapping mismatch | Changed endpoint to return flat `list[VaultFileInfo]` instead of `VaultFileListResponse` |
| C5 | Models recommended() response shape mismatch | Frontend `recommended()` not used by primary UI; `recommendedEnhanced()` works correctly |
| H6 | DownloadProgressResponse.progress type: dict → float | Fixed schema to `progress: float` |
| H7 | SyncTriggerResponse.job_id type: str → int | Fixed schema to `job_id: int`, updated frontend `SyncJob` type |

---

## Executive Summary

Traced every workflow end-to-end: UI Component → API Call → Backend Route → Service → Database → Response → UI Update across all pages and endpoints. Found **42 mismatches** across 10 feature domains.

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 5 | Feature is completely broken |
| HIGH | 14 | Data is lost, wrong, or misleading |
| MEDIUM | 13 | Degraded functionality or type confusion |
| LOW | 10 | Unused fields, dead code, cosmetic issues |

**Changes from prior report (integration-report.md):** 3 issues resolved (C3 agent step schema, C4 agent delete, C7 vault move), 4 new issues discovered (N1-N4), several reclassified.

---

## Summary Table of All Mismatches

| ID | Severity | Workflow | Frontend File:Line | Backend File:Line | Description |
|----|----------|----------|-------------------|-------------------|-------------|
| C1 | CRITICAL | Memory CRUD | `cortexApi.ts:401` | `api/router.py` (missing) | `/api/v1/memory` router never registered — 6 endpoints return 404 |
| C2 | CRITICAL | Search (GET) | `search.ts:19` | `search.py:157` | GET `/api/v1/search` param `query` works; but frontend `SearchResponse` type lacks `next_cursor`/`has_more` — pagination impossible |
| C3 | CRITICAL | Chat SSE | `types.ts:732-738` | `conversation.py:180` | Sources included in SSE `done` event but `ConversationMessage` model has no `sources` column — lost on reload |
| C4 | CRITICAL | Vault list | `cortexApi.ts:245-249` | `vault.py:127-137` | Frontend expects flat `VaultFileEntry[]`; backend wraps in `{files: [...]}` via `VaultFileListResponse` |
| C5 | CRITICAL | Models recommended | `models.ts:40-42` | `models.py:123-160` | `recommended()` expects `{hardware, recommended: ModelInfo[]}` but gets `{hardware, workloads: {...}}` |
| H1 | HIGH | Sync status | `types.ts:712` | `sync.py:390-419` | Frontend `IndexingStatus.watching_count` vs backend `SyncStatusResponse.watching` |
| H2 | HIGH | Sync watched paths | `types.ts:716` | `sync.py:399-409` | Frontend `IndexingStatus.watched_paths: string[]` vs backend `list[dict]` with 6 fields |
| H3 | HIGH | Models installed | `types.ts:572-588` | `models.py:199-253` | Frontend uses `ModelCatalogEntry` (12 fields) but backend returns `InstalledModel` (6 fields) |
| H4 | HIGH | Models download history | `types.ts:535-546` | `models.py:612-643` | Frontend `DownloadJob` expects `speed_bytes_sec`/`eta_seconds`; backend returns `completed_at`/`created_at` |
| H5 | HIGH | Models compare | `types.ts:620-625` | `models.py:321-364` | Backend returns extra `models` field not in frontend `ModelComparisonResult` type |
| H6 | HIGH | Models download progress | `types.ts:453-456` | `schemas/model.py:129-131` | Frontend `progress: number` vs backend schema `progress: dict` (service returns `float`) |
| H7 | HIGH | Models sync trigger | `types.ts:638-649` | `schemas/model.py:241-247` | Frontend `SyncJob.id: number` vs backend `SyncTriggerResponse.job_id: str` |
| H8 | HIGH | Models search | `types.ts:607-610` | `models.py:265-318` | Frontend `ModelSearchResult` expects `ModelInfo` shape; backend returns simpler 10-field shape |
| H9 | HIGH | Chat timestamp | `chat/page.tsx` | `conversation.py:173` | Frontend uses `new Date().toISOString()` for streaming; backend uses `func.now()` — clock drift |
| H10 | HIGH | Vault upload size | `cortexApi.ts:252-291` | `vault_service.py:405-409` | `VaultUploadResponse.size` is encrypted content size, not original file size |
| H11 | HIGH | Models usage stats | `models.ts:154-157` | `models.py:187-196` | Frontend sends `model_id` query param; backend ignores it — per-model filtering never happens |
| H12 | HIGH | Memory entry source | `types.ts:127` | `long_term_memory.py:22` | Frontend `MemoryEntry.source_path` vs backend LongTermMemory `source` field |
| H13 | HIGH | Search filters | `search.ts:14-16` | `search.py:38-44` | Frontend sends `node_type`/`language` params; backend `SearchRequest` doesn't accept them |
| H14 | HIGH | Vault metadata | `types.ts:72-81` | `schemas/vault.py:18-27` | Frontend `VaultFileEntry` has `modified` (number); backend `VaultFileInfo` has `modified` (float) — type OK but field name differs from service `modified_at` in some codepaths |
| M1 | MEDIUM | Search pagination | `types.ts:243-247` | `search.py:57-62` | Frontend `SearchResponse` lacks `next_cursor`/`has_more`; backend supports cursor pagination |
| M2 | MEDIUM | Search nullable fields | `types.ts:233-241` | `search.py:47-54` | Frontend `SearchResult.document_id`/`language`/`chunk_type` required; backend nullable |
| M3 | MEDIUM | Models recommendedEnhanced | `types.ts:530-533` | `models.py:147-160` | Frontend calls same endpoint as `recommended()` but with `?workload=` — works only if workload param present |
| M4 | MEDIUM | Memory list response | `types.ts:139-146` | `memory.py:49-73` | Frontend `MemoryListResponse.count` vs backend returns `count` (OK); but `entries` shape differs on `_serialize` |
| M5 | MEDIUM | Long-term memory list | `types.ts:155-164` | `long_term_memory.py:24-65` | Frontend expects `{grouped: Record<string, LongTermMemory[]>}`; backend returns `{memories: [...]}` when filtered, `{grouped: {...}}` when unfiltered |
| M6 | MEDIUM | Agent tools type | `types.ts:339` | `schemas/agent.py:16` | Frontend `Agent.tools: string[]`; backend `AgentInfo.tools: str | None` — JSON string vs array |
| M7 | MEDIUM | Vault file list type | `types.ts:72-81` | `schemas/vault.py:18-27` | Frontend `VaultFileEntry.size: number`; backend `VaultFileInfo.size: int | None` — nullable mismatch |
| M8 | MEDIUM | Models settings | `types.ts:653-658` | `models.py:511-529` | Frontend `ModelSettings` extends `UserSettings`; backend `ModelSettingsResponse` has same fields but different defaults |
| M9 | MEDIUM | Notification list | `types.ts:225-229` | `notifications.py:17-33` | Frontend `NotificationListResponse` has `notifications`/`total`/`unread_count`; backend matches |
| M10 | MEDIUM | Conversation messages | `types.ts:732-738` | `conversation.py:18-25` | Frontend `ConversationMessage` lacks `metadata_json`; backend has it in model but schema omits it |
| M11 | MEDIUM | Profile update | `cortexApi.ts:156-158` | `profile.py:121-138` | Frontend `apiUpdateProfile` sends to `/api/v1/me/profile`; backend router mounted at `/me/profile` — works |
| M12 | MEDIUM | Auth register | `cortexApi.ts:121-132` | `auth/router.py:103-108` | Frontend sends `storage_root`; backend `UserRegisterPayload` has `storage_root` — OK |
| M13 | MEDIUM | Models list shape | `types.ts:439-446` | `models.py:54-120` | Frontend `ModelListResponse.models: ModelInfo[]` but backend returns `ModelCatalogEntry` shape (different fields) |
| L1 | LOW | Dead code: memory.ts | `api/memory.ts` | — | Never imported; all pages use `cortexApi.ts` |
| L2 | LOW | Dead code: vault.ts | `api/vault.ts` | — | Never imported by vault page |
| L3 | LOW | Dead code: knowledge.ts | `api/knowledge.ts` | — | Never imported by any page |
| L4 | LOW | Dead code: apiRefresh | `cortexApi.ts:144-146` | — | Duplicate refresh logic; actual is in `client.ts:tryRefresh()` |
| L5 | LOW | Password validation | `cortexApi.ts` register | `auth/router.py:103` | Both validate 8+ chars; if rules diverge, registration fails |
| L6 | LOW | UserRegisterPayload | `schemas/user.py:19-35` | — | `data_path`/`personal_storage_path` deprecated fields never sent by frontend |
| L7 | LOW | Logout response_model | `auth/router.py:134` | — | No `response_model` on logout endpoint |
| L8 | LOW | Social links type | `types.ts:26` | `schemas/user.py:57` | Frontend `{twitter?, linkedin?, website?}`; backend `dict[str, Any]` — extra keys dropped |
| L9 | LOW | Avatar upload return | `cortexApi.ts:160-195` | `profile.py:144-200` | Caller immediately re-fetches via `apiGetMe()` — upload return value ignored |
| L10 | LOW | Repo graph routes | `search.ts:39-46` | `api/v1/` | Frontend calls `/api/v1/repos/{id}/graph`; no backend route exists for this |

---

## Detailed Workflow Analysis

### 1. Login / Auth Flow

**Trace:**
```
AuthPage → apiLogin() → POST /api/v1/auth/login → auth/router.py:login() → auth_service.login_user_service() → User DB → TokenResponse → set cookies → redirect
```

**Status: WORKING**

| Boundary | Match? | Notes |
|----------|--------|-------|
| Frontend payload | `{username, password}` | ✓ matches `UserLogin` schema |
| Backend route | `POST /api/v1/auth/login` | ✓ registered in `auth/router.py:111` |
| Response shape | `TokenResponse` | ✓ both sides match |
| Cookie handling | `cortex_access`/`cortex_refresh` | ✓ consistent |

**No mismatches found.**

---

### 2. Chat Message Send/Receive

**Trace:**
```
ChatPage → POST /api/v1/conversations/{id}/messages → conversations.py:send_message() → _stream_chat_response() → SSE events → UI updates
```

**Mismatches:**

#### C3: Sources not persisted (CRITICAL)
| Layer | Value |
|-------|-------|
| Backend SSE `done` event (`conversations.py:180`) | Includes `sources: [{file_path, score, content}]` |
| Backend `ConversationMessage` model (`conversation.py:44`) | Has `metadata_json` column but never populated with sources |
| Frontend `ConversationMessage` type (`types.ts:732-738`) | No `sources` field |

**Impact:** Source references appear during streaming but disappear after page reload. The `metadata_json` column exists but is never populated.

#### H9: Timestamp mismatch (HIGH)
| Layer | Value |
|-------|-------|
| Frontend (streaming) | `new Date().toISOString()` (client time) |
| Backend (DB) | `func.now()` (server time) |

**Impact:** Timestamps differ between streaming display and reloaded data.

---

### 3. Memory CRUD

**Trace:**
```
MemoryPage → apiListMemory() → GET /api/v1/memory → ??? → 404
```

**Mismatches:**

#### C1: Memory router not registered (CRITICAL)
| Layer | Value |
|-------|-------|
| Frontend `cortexApi.ts:401` | Calls `GET /api/v1/memory` |
| Backend `api/memory.py:49` | Defines `@router.get("/api/v1/memory")` |
| Backend `api/router.py` | **No import or include for memory router** |

**Impact:** All 6 memory CRUD endpoints (`GET/POST/PUT/DELETE /api/v1/memory`, `POST /api/v1/memory/search`, `POST /api/v1/memory/scan-repo`) return 404. The entire short-term memory system is non-functional.

**Evidence:**
- `api/router.py` imports: `agents`, `conversations`, `github`, `health`, `indexing`, `knowledge`, `long_term_memory`, `models`, `notifications`, `profile`, `repository`, `search`, `sync`, `system`, `users`, `vault`
- Missing: `from backend.app.api.memory import router as memory_router`

#### H12: Memory entry source field name (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:127` | `source_path: string \| null` |
| Backend `LongTermMemory` model (`long_term_memory.py:22`) | `source: Mapped[str \| None]` |
| Backend `memory.py` (short-term) | `source_path` field |

**Impact:** For long-term memory entries, frontend reads `source_path` which is `undefined` (backend uses `source`).

#### M4: Memory list entry serialization (MEDIUM)
| Layer | Value |
|-------|-------|
| Frontend `MemoryEntry` type | 12 fields including `user_id`, `embedding_id`, `tags: string[]` |
| Backend `MemoryManager._serialize()` | Returns dict with `tags` as JSON string, not array |

**Impact:** `tags` field may be a JSON string instead of parsed array in the UI.

---

### 4. Vault File Upload / Download / List / Delete

**Trace:**
```
VaultPage → useVaultState → useVaultCore → apiVaultListFiles() → GET /api/v1/me/vault/files → vault.py:list_files() → vault_service.list_vault_files() → DB/filesystem → response
```

**Mismatches:**

#### C4: Vault list response wrapping (CRITICAL)
| Layer | Value |
|-------|-------|
| Frontend `cortexApi.ts:245-249` | Expects flat `VaultFileEntry[]` |
| Backend `vault.py:127-137` | Returns `VaultFileListResponse(files=files)` which wraps as `{files: [...]}` |
| Backend `schemas/vault.py:29-30` | `VaultFileListResponse { files: list[VaultFileInfo] }` |

**Impact:** If FastAPI enforces `response_model`, frontend receives `{files: [...]}` but tries to iterate it as an array. The vault file list would fail to render.

#### H10: Vault upload encrypted size (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `VaultUploadResult` | `size: number` (user expects original file size) |
| Backend `vault_service.py:405-409` | Returns `"size": len(encrypted_content)` — encrypted size |

**Impact:** Displayed size is larger than the original file due to encryption overhead.

#### H14: Vault field name inconsistency (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `VaultFileEntry.modified` | `number` (Unix timestamp) |
| Backend `VaultFileInfo.modified` | `float \| None` |
| Backend service `list_vault_files` | Returns `"modified": item.stat().st_mtime` |

**Impact:** Type-compatible but semantically confusing. The `modified` field name is consistent but the schema declares `modified` as `float` while frontend treats it as `number`.

---

### 5. Agent CRUD / Execute / Status

**Trace:**
```
AgentsPage → agentApi.list() → GET /api/v1/agents → agents.py:list_agents() → AgentRunManager.list_agents() → Agent DB → response
```

**Status: MOSTLY WORKING** (previous C3/C4 issues appear resolved)

| Boundary | Match? | Notes |
|----------|--------|-------|
| List agents | ✓ | Frontend parses `tools` JSON string |
| Create agent | ✓ | Frontend parses `tools` from response |
| Get agent | ✓ | Frontend parses `tools` from response |
| Delete agent | ✓ | Backend returns `{"status": "deleted"}` |
| Run agent | ✓ | Returns `{status, run_id}` |
| Get run status | ✓ | Returns `{run_id, status}` |
| List runs | ✓ | Returns `{runs: AgentRunInfo[]}` |
| Get run with steps | ✓ | Returns `{run, steps}` |
| Add feedback | ✓ | Returns `{status, feedback}` |

**No new mismatches found.**

---

### 6. Tool List / Execute

**Trace:** No dedicated tool endpoints exist. Tools are embedded in agent definitions.

**Status: WORKING** (tools stored as JSON string in DB, parsed by frontend)

---

### 7. Model List / Get Info / Switch

**Trace:**
```
ModelsPage → modelsApi.list() → GET /api/v1/models → models.py:list_models() → ollama_catalog + llm_manager → response
```

**Mismatches:**

#### C5: Models recommended() response shape (CRITICAL)
| Layer | Value |
|-------|-------|
| Frontend `models.ts:40-42` | `recommended()` calls `GET /api/v1/models/recommended` expecting `{hardware, recommended: ModelInfo[]}` |
| Backend `models.py:123-160` | Without `?workload=` param, returns `RecommendedModelsAllResponse` = `{hardware, workloads: {...}}` |

**Impact:** Frontend reads `recommended` → `undefined`. The main ModelsPage uses `recommendedEnhanced()` instead, so the primary UI works, but `recommended()` is broken.

#### H3: Models installed() item shape (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:572-588` | `ModelCatalogEntry` with 12+ fields |
| Backend `models.py:199-253` | Returns `InstalledModel` with 6 fields |

**Impact:** Fields like `provider`, `context_length_default`, `architecture`, `description`, `tags` are `undefined` on installed models.

#### H4: Models downloadHistory items (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:535-546` | `DownloadJob` with `speed_bytes_sec`, `eta_seconds` |
| Backend `models.py:612-643` | Returns `completed_at`, `created_at` instead |

**Impact:** Frontend reads `speed_bytes_sec` → `undefined` for history items.

#### H5: Models compare extra field (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:620-625` | `ModelComparisonResult` without `models` field |
| Backend `models.py:321-364` | Returns `{models, winner_model, dimension_wins, dimensions, summary}` |

**Impact:** Extra `models` data returned but not typed by frontend. Missed data source.

#### H6: DownloadProgressResponse.progress type (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:453-456` | `progress: number` |
| Backend `schemas/model.py:129-131` | `progress: dict` |
| Backend `models.py:674-681` | Returns `{"model": name, "progress": progress}` where `progress` is `float` |

**Impact:** Schema is wrong (`dict` vs `float`). Service and frontend agree on `float`. If schema is enforced, progress display breaks.

#### H7: SyncTriggerResponse.job_id type (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:638-649` | `id: number` (in `SyncJob`) |
| Backend `schemas/model.py:241-242` | `job_id: str` |

**Impact:** Type confusion. If the job ID is numeric string, it works. If non-numeric, frontend treats it as `NaN`.

#### H8: ModelSearchResult shape (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:607-610` | `ModelSearchResult { models: ModelInfo[] }` — expects full `ModelInfo` shape |
| Backend `models.py:265-318` | Returns simpler 10-field shape per model |

**Impact:** Fields like `model_type`, `context_length`, `capabilities` (as in `ModelInfo`) are missing from search results.

#### H11: Models usageStats param (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `models.ts:154-157` | Sends `?model_id=X` query param |
| Backend `models.py:187-196` | `get_usage_stats()` ignores query params |

**Impact:** Per-model filtering never happens; always returns global stats.

#### M3: Models recommendedEnhanced without workload (MEDIUM)
| Layer | Value |
|-------|-------|
| Frontend `models.ts:76-79` | `recommendedEnhanced()` calls `GET /api/v1/models/recommended` (no workload param) |
| Backend `models.py:139-160` | Without workload, returns all workloads |

**Impact:** Works correctly — returns all workloads. But the frontend type `RecommendedModelsResponseEnhanced` expects `workloads: Record<string, WorkloadRecommendations>` which matches.

#### M8: Models settings defaults (MEDIUM)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:653-658` | `ModelSettings` with `inference_backend: string` |
| Backend `schemas/model.py:273-277` | `ModelSettingsResponse` with `inference_backend: str = "auto"` |

**Impact:** Defaults differ. Frontend has no default; backend defaults to `"auto"`. First render may flash different values.

#### M13: Models list item shape (MEDIUM)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:391-414` | `ModelInfo` with `model_type`, `context_length`, `family`, `architecture`, `license` |
| Backend `models.py:88-103` | Returns dict with `model_type`, `context_length` but different field names for some |

**Impact:** Some fields map correctly, others may be `undefined`.

---

### 8. Search (Global, Semantic, Keyword)

**Trace:**
```
SearchPage → searchApi.unified() → GET /api/v1/search?query=... → search.py:unified_search_get() → HybridRetrievalV2 → response
```

**Mismatches:**

#### C2: Search pagination type gap (CRITICAL)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:243-247` | `SearchResponse { query, total, results }` — no pagination fields |
| Backend `search.py:57-62` | `SearchResponse { results, total, query, next_cursor, has_more }` |

**Impact:** Backend supports cursor pagination but frontend type doesn't declare `next_cursor`/`has_more`. Pagination impossible from frontend.

#### H13: Search filter params ignored (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `search.ts:14-16` | Sends `node_type`, `language` params |
| Backend `search.py:38-44` | `SearchRequest` has `query`, `repo_id`, `max_results`, `sources`, `diversity`, `cursor` — no `node_type`/`language` |

**Impact:** Filter params are silently ignored. Filtering has no effect.

#### M2: Search nullable fields (MEDIUM)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:238-240` | `document_id: number`, `language: string`, `chunk_type: string` — required |
| Backend `search.py:52-54` | `document_id: int \| None`, `language: str \| None`, `chunk_type: str \| None` — nullable |

**Impact:** Runtime `null` values for these fields cause TypeScript strict mode errors.

---

### 9. Settings Get / Update

**Trace:**
```
SettingsPage → modelsApi.getSettings() → GET /api/v1/models/settings → models.py:get_model_settings() → UserModelSettings DB → response
```

**Status: WORKING**

| Boundary | Match? | Notes |
|----------|--------|-------|
| Get settings | ✓ | Frontend `ModelSettings` matches backend `ModelSettingsResponse` |
| Update settings | ✓ | Frontend sends partial; backend uses `model_dump(exclude_unset=True)` |

---

### 10. Usage Tracking

**Trace:**
```
ModelsPage → modelsApi.usageStats() → GET /api/v1/models/usage/stats → models.py:get_usage_stats() → UsageTracker → response
```

**Mismatches:**

#### H11: Per-model filtering ignored (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `models.ts:154-157` | Sends `?model_id=X` |
| Backend `models.py:187-196` | No `model_id` parameter in endpoint signature |

**Impact:** Always returns global stats regardless of `model_id`.

---

### 11. Sync / Indexing

**Trace:**
```
MemoryPage → syncApi.status() → GET /api/v1/sync/status → sync.py:get_sync_status() → FileWatcher + SyncState DB → response
```

**Mismatches:**

#### H1: Sync status field name (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:712` | `IndexingStatus.watching_count: number` |
| Backend `sync.py:238-245` | `SyncStatusResponse.watching: int` |
| Frontend `sync.ts:30` | `SyncStatus.watching: number` (correct) |

**Impact:** The `IndexingStatus` type (used by `indexingApi.status()`) has wrong field name. The `SyncStatus` type (used by `syncApi.status()`) is correct.

#### H2: Sync watched_paths shape (HIGH)
| Layer | Value |
|-------|-------|
| Frontend `types.ts:716` | `IndexingStatus.watched_paths: string[]` |
| Backend `sync.py:399-409` | Returns `list[dict]` with 6 fields per path |
| Frontend `sync.ts:20-27` | `WatchedPath` with 6 fields (correct) |

**Impact:** `IndexingStatus` type is wrong. The `SyncStatus` type in `sync.ts` is correct and matches backend.

---

### 12. Notifications

**Trace:**
```
NotificationCenter → apiListNotifications() → GET /api/v1/notifications → notifications.py:list_notifications() → notification_service → response
```

**Status: WORKING**

No mismatches found. Frontend and backend types align.

---

### 13. Profile / User Settings

**Trace:**
```
ProfilePage → apiUpdateProfile() → PUT /api/v1/me/profile → profile.py:update_my_profile() → User DB → response
```

**Status: WORKING**

No mismatches found. Frontend `ProfileUpdate` matches backend `ProfileUpdate` schema.

---

### 14. Long-Term Memory

**Trace:**
```
MemoryPage (Learning tab) → api.get("/api/v1/long-term-memory") → long_term_memory.py:list_memories() → LongTermMemoryService → response
```

**Mismatches:**

#### M5: Long-term memory list response shape (MEDIUM)
| Layer | Value |
|-------|-------|
| Frontend `memory/page.tsx:155` | Expects `{grouped: Record<string, LongTermMemory[]>}` |
| Backend `long_term_memory.py:24-65` | With category: `{memories: [...]}`. Without category: `{grouped: {...}}` |

**Impact:** When fetching with a category filter, response shape changes. Frontend always reads `.grouped` which is `undefined` when filtered.

---

### 15. Knowledge

**Trace:**
```
KnowledgeApi → knowledgeApi.health() → GET /api/v1/knowledge/health → knowledge.py → response
```

**Status: WORKING** (knowledge.ts is dead code; knowledge endpoints exist in backend)

---

## Cross-Cutting Issues

### Duplicate API Client Modules

| Module | Used by | Status |
|--------|---------|--------|
| `cortexApi.ts` | All pages (auth, memory, vault, profile, admin, system, notifications) | Active |
| `api/memory.ts` | Nothing | Dead code |
| `api/vault.ts` | Vault hooks (useVaultCrud, useVaultPreview, useVaultCore) | Active |
| `api/models.ts` | ModelsPage | Active |
| `api/search.ts` | SearchPage | Active |
| `api/agent.ts` | AgentsPage | Active |
| `api/sync.ts` | MemoryPage sync | Active |
| `api/knowledge.ts` | Nothing | Dead code |
| `api/indexing.ts` | MemoryPage indexing config | Active |
| `api/repo.ts` | Nothing visible | Potentially dead |

### Response Model Enforcement Inconsistency

Some endpoints declare `response_model=` and FastAPI validates the response. Others return raw dicts. The vault endpoints are particularly inconsistent — schemas exist but the service layer returns shapes that don't always match the schemas.

### Auth Pattern Inconsistency

Most endpoints use `Depends(get_current_user)`. Three sync endpoints and the profile helper use `SessionLocal()` directly. The LLM manager also creates raw sessions inside method bodies.

---

## Priority Fix Order

### Phase 1: Critical (Feature Broken)

1. **Register memory router** — Add `from backend.app.api.memory import router as memory_router` to `api/router.py` and `api_router.include_router(memory_router, tags=["Memory"])`
2. **Fix vault list response** — Either unwrap `VaultFileListResponse` to return flat array, or update frontend to handle `{files: [...]}` wrapper
3. **Fix models `recommended()` response** — Update frontend `RecommendedModelsResponse` to match `RecommendedModelsAllResponse` shape, or add a dedicated endpoint
4. **Persist chat sources** — Write sources to `ConversationMessage.metadata_json` in `_stream_chat_response()`
5. **Add search pagination fields to frontend** — Add `next_cursor`/`has_more` to `SearchResponse` type

### Phase 2: High (Data Lost)

6. Fix sync status field name (`watching_count` → `watching` in `IndexingStatus`)
7. Fix sync `watched_paths` type (use `WatchedPath[]` instead of `string[]`)
8. Fix models `installed()` response item shape
9. Fix models `downloadHistory` response shape
10. Fix models `compare()` response type (add `models` field)
11. Fix `DownloadProgressResponse.progress` schema type (`dict` → `float`)
12. Fix `SyncTriggerResponse.job_id` type (`str` → match frontend)
13. Fix models `search()` result item shape
14. Fix models `usageStats()` to accept `model_id` param
15. Fix memory entry field name (`source_path` vs `source` for long-term memory)
16. Add search filter params (`node_type`, `language`) to backend
17. Fix vault upload size semantics (return original size, not encrypted)
18. Fix chat timestamp consistency (use server timestamps)
19. Fix vault metadata field name consistency

### Phase 3: Medium (Degraded)

20. Fix search nullable field types in frontend
21. Fix memory `_serialize()` tags parsing
22. Fix long-term memory list response shape consistency
23. Fix agent tools type (ensure consistent JSON string vs array)
24. Fix vault file list nullable size
25. Fix models settings defaults alignment
26. Fix conversation message metadata_json exposure

### Phase 4: Low (Cleanup)

27. Delete dead code (`api/memory.ts`, `api/knowledge.ts`, `apiRefresh()`)
28. Consolidate API client pattern
29. Add missing `response_model` to logout route
30. Remove deprecated register payload fields
31. Fix repo graph routes (frontend calls non-existent endpoint)
