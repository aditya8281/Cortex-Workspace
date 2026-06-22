# Cortex Frontend-Backend Integration Report

Generated: 2026-06-22

---

## Executive Summary

Traced every workflow from UI → API → Service → Storage → Response → UI across all 13 pages and 117 backend endpoints. Found **38 mismatches** across 8 feature domains.

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 7 | Feature is completely broken |
| HIGH | 12 | Data is lost, wrong, or misleading |
| MEDIUM | 10 | Degraded functionality or type confusion |
| LOW | 9 | Unused fields, dead code, cosmetic issues |

---

## CRITICAL Mismatches (Feature Broken)

### C1: Search GET parameter `q` vs `query`

| Layer | Value |
|-------|-------|
| Frontend `search.ts:19` | `q` param name |
| Backend `search.py:158` | `query` param name |

**Impact:** `GET /api/v1/search?q=...` returns 422 Validation Error. The primary search path is broken. Only the POST variant (`searchApi.unifiedPost`) works.

---

### C2: No `/api/v1/memory` router exists

| Layer | Route |
|-------|-------|
| Frontend `cortexApi.ts` | `GET/POST/PUT/DELETE /api/v1/memory` |
| Backend `router.py` | No memory router registered |

**Impact:** 6 of 8 memory CRUD endpoints hit 404. The entire short-term memory system (list, create, update, delete, search, scan-repo) is non-functional. The memory page can only load long-term memory data.

---

### C3: AgentStep schema drops all reasoning data

| Layer | Fields |
|-------|--------|
| Backend `serialize_step()` returns | `thought`, `action_input`, `observation` |
| Backend `AgentStepInfo` schema has | `input`, `output` (different names) |
| Frontend `AgentStep` type expects | `thought`, `action_input`, `observation` |

**Impact:** Pydantic v2 silently drops `thought`/`action_input`/`observation` (not in schema) and defaults `input`/`output` to `None`. All agent reasoning data is lost in transit. The run history shows empty steps.

---

### C4: Agent delete returns empty body, frontend expects JSON

| Layer | Response |
|-------|----------|
| Backend `delete_agent()` | No return statement → empty 200 |
| Frontend `agent.ts:61` | Expects `{ status: string }`, calls `res.json()` |

**Impact:** Deletion succeeds on backend but frontend throws JSON parse error. User sees "Failed to delete agent" even though it was deleted.

---

### C5: Vault `list_files` response wrapping mismatch

| Layer | Shape |
|-------|-------|
| Frontend expects | `VaultFileEntry[]` (flat array) |
| Backend service returns | Flat `list[dict]` |
| Backend schema declares | `VaultFileListResponse { files: [...] }` |

**Impact:** If FastAPI enforces `response_model`, parsing fails because a list has no `files` attribute. Works at runtime only because FastAPI passes through unvalidated in some configurations.

---

### C6: Vault `VaultExportResponse` shape mismatch

| Layer | Shape |
|-------|-------|
| Frontend expects | `{ exported: boolean, count: number }` |
| Backend schema | `{ exported: int, destination_dir: str }` |
| Backend service returns | `{ exported: True, count: N }` |

**Impact:** Frontend reads `count` → `undefined`. Schema reads `destination_dir` → `undefined`. Neither layer matches the service output.

---

### C7: Vault `VaultMoveResponse` shape mismatch

| Layer | Shape |
|-------|-------|
| Frontend expects | `{ name: string, path: string }` |
| Backend schema | `{ source_path: str, destination_path: str }` |
| Backend service returns | `{ name: dest.name, path: new_rel }` |

**Impact:** If FastAPI enforces response_model, frontend gets `source_path`/`destination_path` instead of `name`/`path`.

---

## HIGH Mismatches (Data Lost or Wrong)

### H1: Chat sources not persisted to DB

| Layer | Behavior |
|-------|----------|
| Backend SSE `done` event | Includes `sources: [{file_path, score, content}]` |
| Backend `ConversationMessage` model | No `sources` column |
| Frontend `Message` type | Has `sources` field |

**Impact:** Source references appear during streaming but disappear after page reload. The `metadata_json` column exists but is never populated with sources.

---

### H2: Chat `created_at` timestamp mismatch

| Layer | Value |
|-------|-------|
| Frontend (streaming) | `new Date().toISOString()` (client time) |
| Backend (DB) | `func.now()` (server time) |

**Impact:** Timestamps differ between streaming display and reloaded data. Usually milliseconds apart but could drift if clock sync is off.

---

### H3: Vault field name mismatches (`modified` vs `modified_at`)

| Layer | Field names |
|-------|-------------|
| Frontend `VaultFileEntry` | `modified`, `created`, `favorite`, `tags` |
| Backend `VaultFileInfo` schema | `modified_at`, `created_at` (no `favorite`, `tags`) |
| Backend service returns | `modified`, `created`, `favorite`, `tags` |

**Impact:** Schema drops `favorite`/`tags`. Field names differ between schema and service. Frontend reads `modified` which works if schema is not enforced.

---

### H4: Agent `AgentRunInfo` drops `error` and `completed_at`

| Layer | Fields |
|-------|--------|
| Backend `serialize_run()` returns | `error`, `completed_at` |
| Backend `AgentRunInfo` schema | Missing both fields |
| Frontend `AgentRun` type expects | `error`, `completed_at` |

**Impact:** Agent run errors and completion timestamps are silently dropped by Pydantic. Frontend always sees `undefined`.

---

### H5: Agent `create()` doesn't parse tools JSON

| Layer | Behavior |
|-------|----------|
| `agentApi.list()` | `JSON.parse(a.tools)` ✓ |
| `agentApi.get()` | `JSON.parse(res.agent.tools)` ✓ |
| `agentApi.create()` | No parsing ✗ |

**Impact:** Created agent has tools as JSON string `'["search"]'` instead of array `["search"]`. Iterating over it yields characters instead of elements.

---

### H6: Models `recommended()` response shape mismatch

| Layer | Shape |
|-------|-------|
| Frontend `modelsApi.recommended()` | `{ hardware, recommended: ModelInfo[] }` |
| Backend (no workload param) | `{ hardware, workloads: { [key]: WorkloadRecommendations } }` |

**Impact:** Frontend reads `recommended` → `undefined`. The main ModelsPage uses `recommendedEnhanced()` instead, so the primary UI works, but `recommended()` is broken.

---

### H7: Models `DownloadProgressResponse.progress` type mismatch

| Layer | Type |
|-------|------|
| Frontend | `number` |
| Backend schema | `dict` |
| Backend service | `float` |

**Impact:** Schema is wrong. Service and frontend agree. If schema is enforced, progress display breaks.

---

### H8: Sync status `watching_count` vs `watching`

| Layer | Field name |
|-------|-----------|
| Frontend `IndexingStatus` | `watching_count` |
| Backend `SyncStatusResponse` | `watching` |

**Impact:** `IndexingConfigForm` displays `undefined` for the watching count.

---

### H9: Sync `watched_paths` type mismatch

| Layer | Type |
|-------|------|
| Frontend `WatchedPath` | `{ path, repo_id, embedding_model, sync_enabled, initial_scan_job_id, initial_scan_status }` |
| Backend response | `[{ path, status }]` |

**Impact:** Frontend expects 6 fields per path, backend returns 2. All fields except `path` are `undefined`. `watched_paths` renders as `[object Object]` in some UI code.

---

### H10: Memory `MemoryEntry.source_path` vs `source`

| Layer | Field name |
|-------|-----------|
| Frontend | `source_path` |
| Backend | `source` |

**Impact:** Source path is `undefined` in the UI.

---

### H11: Models `installed()` response item shape

| Layer | Item shape |
|-------|-----------|
| Frontend uses | `ModelCatalogEntry` (12 fields) |
| Backend returns | `InstalledModel` (6 fields) |

**Impact:** Fields like `provider`, `context_length_default`, `architecture`, `description`, `tags` are `undefined` on installed models.

---

### H12: Models `SyncTriggerResponse.job_id` type

| Layer | Type |
|-------|------|
| Frontend | `number` |
| Backend schema | `str` |

**Impact:** Type confusion. If the job ID is numeric, it works. If string, frontend treats it as `NaN`.

---

## MEDIUM Mismatches (Degraded Functionality)

### M1: Search `node_type`/`language` params sent but ignored

Frontend sends filter params that backend doesn't accept. Filtering has no effect.

---

### M2: Search response missing `next_cursor`/`has_more` in frontend type

Backend supports cursor pagination but frontend type doesn't declare these fields. Pagination impossible.

---

### M3: Search `SearchResult` nullable fields typed as required

`document_id`, `language`, `chunk_type` are nullable in backend but required in frontend type. Potential runtime null.

---

### M4: Models `usageStats(modelId)` param ignored

Frontend sends `model_id` query param. Backend has no such parameter. Per-model filtering never happens.

---

### M5: Models `ModelSearchResult` items missing fields

Frontend expects `ModelInfo` shape (with `model_type`, `context_length`, etc.) but backend search returns simpler shape.

---

### M6: Models `ModelComparisonResult` missing `models` field

Backend returns extra `models` data that frontend type doesn't declare. Missed data source.

---

### M7: Models `downloadHistory` items mismatch

Frontend expects `speed_bytes_sec`/`eta_seconds`. Backend returns `completed_at`/`created_at` instead.

---

### M8: Memory list response shape mismatch

Frontend expects `{ entries, total, categories }`. Backend returns `{ memories }` or `{ grouped }`.

---

### M9: Memory create payload `source_path` vs `source`

Frontend sends `source_path`. Backend expects `source`.

---

### M10: Vault upload returns encrypted size, not original

`VaultUploadResponse.size` is the encrypted content size, not the original file size. Misleading to users.

---

## LOW Mismatches (Cosmetic / Dead Code)

### L1: `vault.ts` is dead code

`vaultApi` module exists but vault page uses `cortexApi.ts` exclusively. Never imported.

---

### L2: `memory.ts` is dead code

`memoryApi` module exists but memory page uses `cortexApi.ts` functions. Never imported.

---

### L3: `apiRefresh()` in cortexApi.ts is dead code

Actual refresh logic is in `client.ts:tryRefresh()`. Two implementations of same concept.

---

### L4: Frontend password validation duplicates backend

Both sides validate 8 chars + letter + number. If rules change on one side, they diverge.

---

### L5: `apiUploadAvatar()` return value always ignored

Caller immediately re-fetches via `apiGetMe()`. Unnecessary network request.

---

### L6: Create conversation frontend type mismatch

Frontend expects `{ id: number }` but receives full `ConversationResponse`. Works due to structural typing.

---

### L7: Logout route has no `response_model`

OpenAPI schema won't document the response. Minor API documentation gap.

---

### L8: `UserRegisterPayload` has deprecated fields

`data_path`, `personal_storage_path` are never sent by frontend. Dead schema fields.

---

### L9: Frontend `social_links` type narrower than backend

Frontend: `{ twitter?, linkedin?, website? }`. Backend: `dict[str, Any]`. Extra keys silently dropped.

---

## Cross-Cutting Issues

### Duplicate API Client Modules

| Module | Used by | Status |
|--------|---------|--------|
| `cortexApi.ts` | All pages | Active |
| `api/memory.ts` | Nothing | Dead code |
| `api/vault.ts` | Nothing | Dead code |
| `api/models.ts` | ModelsPage | Active |
| `api/search.ts` | SearchPage | Active |
| `api/agent.ts` | AgentsPage | Active |
| `api/sync.ts` | MemoryPage sync | Active |
| `api/knowledge.ts` | Nothing | Dead code |

**Issue:** Two parallel patterns exist — centralized `cortexApi.ts` and domain-specific `api/*.ts` modules. Some pages use one, some use the other. This creates confusion about which to use for new features.

---

### Response Model Enforcement Inconsistency

Some endpoints declare `response_model=` and FastAPI validates the response. Others return raw dicts. The vault endpoints are particularly inconsistent — schemas exist but the service layer returns shapes that don't match the schemas.

---

### Auth Pattern Inconsistency

Most endpoints use `Depends(get_current_user)`. Three sync endpoints and the profile helper use `SessionLocal()` directly. The LLM manager also creates raw sessions inside method bodies.

---

## Priority Fix Order

### Phase 1: Critical (Feature Broken)

1. Fix search GET parameter name (`q` → `query`)
2. Register `/api/v1/memory` router or redirect frontend to correct endpoints
3. Fix agent step schema (`AgentStepInfo` fields)
4. Fix agent delete response (add return statement)
5. Fix vault response models (align schemas with service output)

### Phase 2: High (Data Lost)

6. Persist chat sources to `metadata_json` column
7. Fix agent run schema (add `error`, `completed_at`)
8. Fix agent create tools parsing
9. Fix sync status field names (`watching_count` → `watching`)
10. Fix sync `watched_paths` shape (return full data or simplify frontend type)
11. Fix memory entry field names (`source_path` → `source`)
12. Fix models `recommended()` response shape
13. Fix models `installed()` response item shape

### Phase 3: Medium (Degraded)

14. Add search filter params to backend
15. Add cursor pagination to frontend search type
16. Fix models `usageStats` param handling
17. Fix models `downloadHistory` response shape
18. Fix memory list response shape alignment
19. Fix vault upload size semantics

### Phase 4: Low (Cleanup)

20. Delete dead code (`vault.ts`, `memory.ts`, `apiRefresh()`)
21. Consolidate API client pattern
22. Add missing `response_model` to logout route
23. Remove deprecated register payload fields
