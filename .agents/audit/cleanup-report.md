# Cortex Codebase Cleanup Report

Generated: 2026-06-22

---

## Executive Summary

| Category | Count | Lines |
|----------|-------|-------|
| Dead backend files | 12 | ~3,500 |
| Dead frontend files | 16 | ~3,200 |
| Dead functions/methods | 22 | ~400 |
| Dead frontend exports | 21 | ~325 |
| Duplicate code patterns | 18 | ~800 |
| **Total cleanup items** | **89** | **~8,225** |

---

## Part 1: Dead Backend Files (12 files, ~3,500 lines)

| # | File | Lines | Reason Dead | Safe to Remove |
|---|------|-------|-------------|----------------|
| B1 | `services/file_watcher.py` | 289 | Legacy v1, superseded by `file_watcher_v2.py` | Yes |
| B2 | `services/threaded_scanner.py` | 234 | Experiment, never integrated | Yes |
| B3 | `services/batch_indexer.py` | 172 | Never imported anywhere | Yes |
| B4 | `services/cross_file_search.py` | 166 | Superseded by `hybrid_retrieval.py` | Yes |
| B5 | `services/deletion_pipeline.py` | 155 | Built but never wired to any API | Yes |
| B6 | `services/document_statistics.py` | 172 | Never wired to any API | Yes |
| B7 | `services/indexing_orchestrator.py` | 99 | Experiment, never connected | Yes |
| B8 | `services/search_clustering.py` | 44 | Never integrated | Yes |
| B9 | `services/path_index.py` | 276 | Service dead; model exists but unused | Yes |
| B10 | `services/model_detail_scraper.py` | 264 | Test-only, no production use | Yes |
| B11 | `services/seed_data.py` | 295 | Test-only, no production use | Yes |
| B12 | `services/entity_extractor.py` | 220 | Only called from dead `graph_builder.build_document_graph()` | Yes |

---

## Part 2: Dead Frontend Files (16 files, ~3,200 lines)

| # | File | Lines | Reason Dead | Safe to Remove |
|---|------|-------|-------------|----------------|
| F1 | `app/models/styles.css` | 1,697 | Pre-Tailwind CSS, all components use Tailwind now | Yes |
| F2 | `src/shared/api/vault.ts` | ~60 | Duplicate of `cortexApi.ts` vault functions | Yes |
| F3 | `src/shared/api/memory.ts` | ~60 | Duplicate of `cortexApi.ts` memory functions | Yes |
| F4 | `src/shared/api/repo.ts` | ~50 | Repository management UI removed | Yes |
| F5 | `src/shared/api/knowledge.ts` | ~20 | Never imported | Yes |
| F6 | `app/search/SearchFilters.tsx` | ~80 | Orphaned from search page rewrite | Yes |
| F7 | `app/search/SearchResults.tsx` | ~100 | Orphaned from search page rewrite | Yes |
| F8 | `app/search/GraphView.tsx` | ~150 | Abandoned graph visualization feature | Yes |
| F9 | `app/models/InstalledModelsPanel.tsx` | ~80 | Superseded by current ModelsPage | Yes |
| F10 | `app/models/DownloadQueuePanel.tsx` | ~80 | Superseded by current ModelsPage | Yes |
| F11 | `app/models/ModelBrowser.tsx` | ~200 | Older model browsing UI | Yes |
| F12 | `app/models/HardwareOverview.tsx` | ~60 | Superseded by `HardwareBar.tsx` | Yes |
| F13 | `app/models/components/CompareModal.tsx` | ~150 | Abandoned model comparison experiment | Yes |
| F14 | `app/models/components/CompareTray.tsx` | ~80 | Abandoned model comparison experiment | Yes |
| F15 | `src/shared/ui/StaggerChildren.tsx` | ~30 | Never imported | Yes |
| F16 | `src/shared/ui/Steps.tsx` | ~40 | Never imported | Yes |

---

## Part 3: Dead Functions & Methods (22 items, ~400 lines)

### Backend Dead Methods

| # | Location | Function | Reason Dead |
|---|----------|----------|-------------|
| M1 | `embedding_service.py:169` | `embed_with_cache()` | Never called |
| M2 | `graph_builder.py:114` | `build_document_graph()` | Never called |
| M3 | `llm/manager.py:303` | `refresh_ollama_catalog()` | Never called |
| M4 | `long_term_memory.py:51` | `decay()` | Never scheduled or triggered |
| M5 | `embedding_cache.py:110` | `cleanup_expired()` | Never triggered |
| M6 | `memory_manager.py:204` | `consolidate_from_conversation()` | Never called |
| M7 | `rag_pipeline.py:117` | `consolidate()` | Never called |
| M8 | `hardware.py:318` | `estimate_vram_for_gpu()` | Test-only |
| M9 | `tasks/worker.py:23` | `sample_task` | Demo-only, never enqueued |

### Frontend Dead Exports

| # | Location | Export | Reason Dead |
|---|----------|--------|-------------|
| M10 | `cortexApi.ts` | `apiRefresh()` | Superseded by `client.ts:tryRefresh()` |
| M11 | `cortexApi.ts` | `apiGetMemory(id)` | Never imported |
| M12 | `cortexApi.ts` | `apiScanRepo()` | Never imported |
| M13 | `cortexApi.ts` | `apiMarkNotificationRead()` | No notification UI |
| M14 | `cortexApi.ts` | `apiMarkAllNotificationsRead()` | No notification UI |
| M15 | `cortexApi.ts` | `apiDeleteNotification()` | No notification UI |
| M16 | `search.ts` | `searchApi.unifiedPost()` | Never called |
| M17 | `search.ts` | `searchApi.getGraph()` | Only used by dead `GraphView.tsx` |
| M18 | `search.ts` | `searchApi.getNodeContext()` | Only used by dead `GraphView.tsx` |
| M19 | `models.ts` | `modelsApi.health()` | Never called |
| M20 | `models.ts` | `modelsApi.metrics()` | Never called |
| M21 | `models.ts` | `modelsApi.sync()` | Never called |
| M22 | `models.ts` | `modelsApi.syncStatus()` | Never called |

---

## Part 4: Duplicate Code Patterns (18 patterns, ~800 lines)

### Critical Duplicates

| # | Pattern | Location | Lines | Fix |
|---|---------|----------|-------|-----|
| D1 | Two frontend API client systems | `cortexApi.ts` + 10 `shared/api/*.ts` | ~600 | Consolidate to one |
| D2 | `get_current_user`/`get_db` import paths | 15 files across `core.db` / `api.deps` | - | Standardize imports |

### Moderate Duplicates

| # | Pattern | Location | Occurrences | Fix |
|---|---------|----------|-------------|-----|
| D3 | Repository ownership check | `repository.py` | 8x | Extract helper |
| D4 | Agent run ownership check | `agents.py` | 6x | Extract helper |
| D5 | System metrics collection | `system.py` + `ws_system.py` | 2x | Extract shared function |
| D6 | Vault metadata path remapping | `vault_service.py` | 2x (~25 lines each) | Extract helper |
| D7 | Auth router manual token extraction | `auth/router.py` | 4x | Use `Depends(get_current_user)` |
| D8 | `indexingApi.status()` = `syncApi.status()` | `indexing.ts` + `sync.ts` | 2x | Remove duplicate |

### Minor Duplicates

| # | Pattern | Location | Occurrences | Fix |
|---|---------|----------|-------------|-----|
| D9 | Vault path traversal guard | `vault_service.py` | 9x | Extract `_safe_resolve()` |
| D10 | Vault hidden-file filter | `vault_service.py` | 4x | Extract predicate |
| D11 | SSE streaming headers | `agents.py` + `conversations.py` | 2x | Extract constant |
| D12 | WebSocket auth boilerplate | `ws_models.py` + `ws_system.py` | 2x | Extract helper |
| D13 | Fetch+retry pattern | `cortexApi.ts` | 5x | Extract utility |
| D14 | Ollama httpx client | `models.py` | 3x | Extract factory |
| D15 | Memory category constants | `long_term_memory.py` + `memory.py` | 2x | Unify |
| D16 | `detail()` = `getModelDetail()` | `models.ts` | 2x | Remove alias |
| D17 | `usageStats()` = `getUsageStats()` | `models.ts` | 2x | Remove alias |
| D18 | Profile photo URL path | `cortexApi.ts` + `profile.py` | 2x | Use constant |

---

## Part 5: Cleanup Priority Order

### Phase 1: Delete Dead Files (Low risk, high volume)

Delete all 12 dead backend files and 16 dead frontend files. These are completely unused and removing them reduces cognitive load without any behavioral change.

**Estimated impact:** -6,700 lines, zero risk.

### Phase 2: Remove Dead Functions (Low risk)

Remove the 22 dead functions/methods identified in Part 3. These are defined but never called.

**Estimated impact:** -400 lines, zero risk.

### Phase 3: Consolidate API Clients (Medium risk)

The `cortexApi.ts` vs `shared/api/*.ts` duplication is the single biggest source of confusion. Pick one pattern and consolidate:
- Option A: Keep `cortexApi.ts` as the single API layer, delete `shared/api/*.ts` duplicates
- Option B: Move everything to `shared/api/*.ts` modules, delete `cortexApi.ts`

**Estimated impact:** -600 lines, low risk (behavioral change: none, just organization).

### Phase 4: Extract Duplicated Helpers (Low risk)

Extract the repeated patterns into shared helpers:
- `_require_repo_owner()` dependency
- `_require_run_owner()` dependency
- `_safe_resolve()` for vault path traversal
- `_remap_metadata_paths()` for vault rename/move
- `_SSE_HEADERS` constant
- `_ws_authenticate()` helper

**Estimated impact:** -400 lines, low risk.

### Phase 5: Standardize Import Paths (Zero risk)

Standardize all route files to import from `core.db` (remove `api/deps.py` re-export shim) OR from `api/deps.py` (update all to use it). Pick one.

**Estimated impact:** Zero lines changed, zero risk.

---

## Part 6: What NOT to Delete

| Item | Why Keep |
|------|----------|
| `services/seed_data.py` | Test infrastructure; move to `tests/fixtures/` instead of deleting |
| `services/model_detail_scraper.py` | Test infrastructure; move to `tests/fixtures/` instead of deleting |
| `api/deps.py` | Active re-export shim used by 7 route files; standardize imports first |
| `models/PathIndex` model | Has Alembic migration; remove model + migration in a separate PR |
| Notification CRUD functions in `cortexApi.ts` | Infrastructure for future notification UI; keep until notification sources exist |
| `services/long_term_memory.py` `decay()` | Intentional feature, just needs a cron job; keep and schedule |
| `services/embedding_cache.py` `cleanup_expired()` | Intentional feature, just needs a cron job; keep and schedule |
