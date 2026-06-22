# Cortex Codebase Cleanup Audit

**Date:** 2026-06-22
**Updated:** 2026-06-22 (P0/P1 fixes applied)
**Scope:** Full codebase — frontend/, backend/, cli/, tests/

---

## Fixed Issues (2026-06-22)

| Issue | Fix |
|-------|-----|
| Unused import `pathlib.Path` in `executor.py` | Removed unused import |
| Unused import `VaultFileListResponse` in `vault.py` | Removed after vault list response fix |

## Fixed Issues — Session 3 (2026-06-22)

| Issue | Fix |
|-------|-----|
| Redundant `auth/security.py` re-export (M4) | Deleted file — all imports updated to `core.security` |
| Unused UI components: `Tooltip.tsx`, `StaggerChildren.tsx`, `Steps.tsx` (M7, M8, M11) | Deleted all 3 files |
| CLI stubs — entire `cli/` directory non-functional (H5) | Deleted `cli/` directory (15 command stubs + entry point) |

---

---

## Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Dead Code (unused services/functions) | 0 | 8 | 6 | 2 | 16 |
| Dead Frontend Components | 0 | 3 | 1 | 0 | 4 |
| Duplicate API Patterns | 0 | 2 | 1 | 0 | 3 |
| Stub/Unimplemented Code | 0 | 1 | 0 | 0 | 1 |
| Dead Imports/Re-exports | 0 | 0 | 2 | 1 | 3 |
| Legacy/Deprecated Code | 0 | 0 | 1 | 1 | 2 |
| **Totals** | **0** | **14** | **11** | **4** | **29** |

---

## CRITICAL — Actively Harmful

None identified. No security vulnerabilities or actively breaking code found.

---

## HIGH — Significant Waste

### H1: Dead Backend Services (0 production imports)

These service files exist but are never imported by any production code (only referenced in tests or not at all):

| File | Lines | Notes |
|------|-------|-------|
| `backend/app/services/cross_file_search.py` | 150+ | Class `CrossFileSearch` defined, zero imports in production |
| `backend/app/services/search_clustering.py` | 60+ | Class `SearchClusterer` defined, zero imports in production |
| `backend/app/services/threaded_scanner.py` | 234 | Class `ThreadedScanner` defined, zero imports in production |
| `backend/app/services/batch_indexer.py` | 100+ | Class `BatchIndexer` defined, zero imports in production |
| `backend/app/services/document_statistics.py` | 100+ | Class `DocumentStatistics` defined, zero imports in production |
| `backend/app/services/path_index.py` | 100+ | Class `PathIndexer` defined, zero imports in production |
| `backend/app/services/model_detail_scraper.py` | 200+ | Class `ModelDetailScraper` defined, only imported in tests |
| `backend/app/services/indexing_orchestrator.py` | 100+ | Class `IndexingOrchestrator` defined, only self-referencing |

**Impact:** ~1000+ lines of dead code. These services were likely built for future use or abandoned mid-implementation.

### H2: Dead Frontend Components (search page)

The following components in `frontend/app/search/` are **never imported** by the search page or any other file:

| File | Lines | Status |
|------|-------|--------|
| `frontend/app/search/GraphView.tsx` | 213 | Never imported — search page uses inline rendering |
| `frontend/app/search/SearchFilters.tsx` | 107 | Never imported — search page has its own filter UI |
| `frontend/app/search/SearchResults.tsx` | 106 | Never imported — search page renders results inline |

**Impact:** 426 lines of dead React components. The search page (`page.tsx`) was rewritten to use a simpler inline approach, making these components orphaned.

### H3: Duplicate Memory API (cortexApi.ts vs shared/api/memory.ts)

Two separate API clients exist for the same memory endpoints:

- `frontend/src/shared/auth/cortexApi.ts` — exports `apiListMemory`, `apiSearchMemory`, `apiCreateMemory`, `apiUpdateMemory`, `apiDeleteMemory`
- `frontend/src/shared/api/memory.ts` — exports `memoryApi` with `.list()`, `.search()`, `.create()`, `.update()`, `.delete()`

Both call identical backend endpoints (`/api/v1/memory`). The memory page uses `cortexApi` functions; the dashboard uses `memoryApi`.

**Impact:** Confusing dual API surface. Maintenance burden — changes must be made in two places.

### H4: Duplicate API Patterns (profile/settings)

`cortexApi.ts` contains profile functions (`apiGetMe`, `apiUpdateProfile`, `apiUploadAvatar`, etc.) that overlap with what could be a `profileApi` in `shared/api/`. The codebase has a mixed pattern: some domains use `shared/api/*.ts` modules, others use the monolithic `cortexApi.ts`.

### H5: Entire CLI is Stub Code (158 lines)

All 15 commands in `cli/src/commands/` are unimplemented stubs:

```
backup, build, deploy, dev, doctor, init, install, logs,
migrate, registry, setup, start, status, stop, update
```

Each simply logs "not yet implemented" and exits. The CLI entry point (`cli/src/index.ts`, 116 lines) wires them up but nothing works.

**Impact:** 274 lines of completely non-functional code shipped in the repo.

### H6: Dead Service — seed_data.py

`backend/app/services/seed_data.py` (100+ lines) defines seed data for providers/quantizations but is **never imported** by any production code. Only referenced in `tests/test_seed_data.py`.

### H7: Dead Service — deletion_pipeline.py

`backend/app/services/deletion_pipeline.py` defines `DeletionPipeline` class but is **never imported** by any production code. Only referenced in `tests/test_deletion_pipeline.py`.

### H8: Duplicate chunker implementations

Two chunking systems coexist:
- `backend/app/services/chunker.py` — used by `repo_scanner`, `incremental_indexer`, `file_watcher_v2`, `indexing_rules`
- `backend/app/services/semantic_chunker.py` — used by `document_indexer`

Both serve similar purposes (splitting documents into chunks) with different approaches. The semantic chunker is only used in one place.

---

## MEDIUM — Should Clean

### M1: Unused `service_base.py`

`backend/app/core/service_base.py` is imported by **zero files** in the codebase. Dead module.

### M2: Unused `path_index.py` model

`backend/app/models/path_index.py` defines the `PathIndex` SQLAlchemy model. The corresponding service `backend/app/services/path_index.py` is dead (see H1). The model itself is only used within the dead service.

### M3: Unused `notification_extra.py` schema

`backend/app/schemas/notification_extra.py` defines `NotificationOkResponse` and `NotificationMarkReadResponse` — used only by `notifications.py` endpoint. While technically used, these trivial schemas (2 fields each) could be inlined.

### M4: Redundant `auth/security.py` re-export

`backend/app/auth/security.py` is a 3-line file that re-exports from `backend.app.core.security`:
```python
from backend.app.core.security import hash_password, validate_password_strength, verify_password
```
Nothing imports from `auth/security.py` — all code imports directly from `core/security.py`.

### M5: `tauri-adapter.ts` is dead code

`frontend/src/shared/services/folder-picker/tauri-adapter.ts` contains a `TauriFolderPicker` class that throws "not yet implemented" on every call. The `isSupported()` method returns `false`. This is an abandoned Tauri desktop integration experiment.

### M6: `WorkloadRecommendations` in memory page

`frontend/app/memory/page.tsx` imports `WorkloadRecommendations` type but the memory page doesn't display workload recommendations — this type is only used by the models page.

### M7: Unused `Tooltip.tsx` component

`frontend/src/shared/ui/Tooltip.tsx` exists but is never imported by any other file (only referenced inside `GraphView.tsx` which is itself dead — see H2).

### M8: Unused `StaggerChildren.tsx` component

`frontend/src/shared/ui/StaggerChildren.tsx` exists but is never imported by any file.

### M9: Duplicate `getCsrfToken` implementations

`getCsrfToken` is defined in both:
- `frontend/src/shared/auth/cortexApi.ts` (line 53)
- `frontend/src/shared/api/client.ts`

The cortexApi version is used by cortexApi functions; the client.ts version is used by direct `api` calls.

### M10: Duplicate `api` vs `cortexApi` HTTP patterns

`cortexApi.ts` implements its own HTTP client with CSRF handling, while `shared/api/client.ts` provides a separate `api` object. Both make HTTP calls but with different patterns.

### M11: Unused `Steps.tsx` component

`frontend/src/shared/ui/Steps.tsx` exists but is never imported by any file (only appears in `AgentChat.tsx` as unrelated step-related variable names).

---

## LOW — Nice to Have

### L1: TODO/FIXME comments

| File | Line | Comment |
|------|------|---------|
| `frontend/src/shared/services/folder-picker/tauri-adapter.ts` | 15 | `// TODO: Uncomment when @tauri-apps/api is installed` |
| `frontend/app/page.tsx` | 186 | `href="#" // TODO: Replace with actual Cortex GitHub repo URL` |

### L2: `DEPRECATED` schema aliases

`backend/app/schemas/user.py:32` — contains deprecated field aliases kept for backward compatibility. May be safe to remove if no old clients exist.

### L3: `file_watcher.py` vs `file_watcher_v2.py`

The original `file_watcher.py` (289 lines) is superseded by `file_watcher_v2.py`. Production code only uses v2. The old file is dead but kept in the repo.

### L4: Tiny `__init__.py` files

Several `__init__.py` files are empty (0 bytes) — standard Python convention, not actionable.

---

## Duplicate Endpoints

### D1: Memory endpoints — dual registration

The memory API is registered in **two places**:
- `backend/app/api/memory.py` — registered directly in `main.py:210` as `app.include_router(memory_router)`
- `backend/app/api/v1/long_term_memory.py` — registered via `api_router` in `router.py:55`

Both handle `/api/v1/memory/*` routes but for different purposes (short-term notes vs long-term memory). The naming and proximity creates confusion.

### D2: Search endpoint — GET and POST

`backend/app/api/v1/search.py` exposes both:
- `GET /search` (line 155)
- `POST /search` (line 65)

Both perform the same unified search. The GET version is a convenience wrapper.

---

## Unused Files Summary

| File | Type | Reason |
|------|------|--------|
| `frontend/app/search/GraphView.tsx` | Component | Never imported |
| `frontend/app/search/SearchFilters.tsx` | Component | Never imported |
| `frontend/app/search/SearchResults.tsx` | Component | Never imported |
| `frontend/src/shared/ui/Tooltip.tsx` | Component | Never imported (dead deps) |
| `frontend/src/shared/ui/StaggerChildren.tsx` | Component | Never imported |
| `frontend/src/shared/ui/Steps.tsx` | Component | Never imported |
| `frontend/src/shared/services/folder-picker/tauri-adapter.ts` | Service | Abandoned experiment |
| `backend/app/services/cross_file_search.py` | Service | Zero production imports |
| `backend/app/services/search_clustering.py` | Service | Zero production imports |
| `backend/app/services/threaded_scanner.py` | Service | Zero production imports |
| `backend/app/services/batch_indexer.py` | Service | Zero production imports |
| `backend/app/services/document_statistics.py` | Service | Zero production imports |
| `backend/app/services/path_index.py` | Service | Zero production imports |
| `backend/app/services/model_detail_scraper.py` | Service | Only test imports |
| `backend/app/services/indexing_orchestrator.py` | Service | Only self-references |
| `backend/app/services/seed_data.py` | Service | Only test imports |
| `backend/app/services/deletion_pipeline.py` | Service | Only test imports |
| `backend/app/core/service_base.py` | Module | Zero imports |
| `backend/app/auth/security.py` | Module | Zero imports (re-export) |
| `backend/app/services/file_watcher.py` | Service | Superseded by v2 |
| `cli/src/commands/*.ts` (15 files) | CLI | All stubs, zero functionality |

---

## Abandoned Experiments

1. **Tauri desktop integration** — `tauri-adapter.ts` + `folder-picker/` types. Desktop app wrapper was planned but never completed.
2. **CLI tool** — 15 command stubs suggest a CLI was designed but never implemented.
3. **Graph view for search** — `GraphView.tsx` (213 lines) suggests a code graph visualization was built then abandoned in favor of a simpler search UI.
4. **Cross-file search with graph enrichment** — `cross_file_search.py` was built to combine semantic search with code graph context, but was never wired up.

---

## Recommendations

1. **Immediate cleanup (High impact):**
   - Delete `frontend/app/search/GraphView.tsx`, `SearchFilters.tsx`, `SearchResults.tsx`
   - Delete dead backend services: `cross_file_search.py`, `search_clustering.py`, `threaded_scanner.py`, `batch_indexer.py`, `document_statistics.py`, `path_index.py`, `model_detail_scraper.py`, `indexing_orchestrator.py`, `seed_data.py`, `deletion_pipeline.py`
   - Delete `backend/app/core/service_base.py`, `backend/app/auth/security.py`
   - Consolidate memory API: remove duplicate functions from `cortexApi.ts` or `shared/api/memory.ts`

2. **Short-term (Medium impact):**
   - Delete or mark CLI as experimental/removed
   - Delete `tauri-adapter.ts` and related folder-picker types if Tauri is not planned
   - Delete unused UI components: `Tooltip.tsx`, `StaggerChildren.tsx`, `Steps.tsx`
   - Remove `file_watcher.py` (superseded by v2)

3. **Nice-to-have (Low impact):**
   - Resolve TODO comments
   - Remove deprecated schema aliases if no backward compat needed
   - Consolidate `cortexApi.ts` into domain-specific API modules
