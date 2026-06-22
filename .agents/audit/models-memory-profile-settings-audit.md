# Comprehensive Audit: Models, Memory, Profile, Settings Pages

**Audit Date:** 2026-06-22
**Auditor:** Automated Code Audit

---

## Table of Contents

1. [Models Page](#1-models-page)
2. [Model Detail Page](#2-model-detail-page)
3. [Downloads Page](#3-downloads-page)
4. [Memory Page](#4-memory-page)
5. [Profile Page](#5-profile-page)
6. [Settings Page](#6-settings-page)
7. [Migration Chain Audit](#7-migration-chain-audit)

---

## 1. Models Page

### File Paths

| File | Path | Lines |
|------|------|-------|
| Main Page | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/ModelsPage.tsx` | 244 |
| Models Page Router | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/page.tsx` | (wrapper) |
| HardwareBar | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/components/HardwareBar.tsx` | 64 |
| CatalogTable | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/components/CatalogTable.tsx` | 170 |
| TopPicksCarousel | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/components/TopPicksCarousel.tsx` | 120 |
| WorkloadColumns | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/components/WorkloadColumns.tsx` | — |
| InstalledBar | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/components/InstalledBar.tsx` | 83 |
| Frontend API Client | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/api/models.ts` | 178 |
| Backend Router | `/home/adi/Desktop/Cortex-Workspace/backend/app/api/v1/models.py` | 1001 |

### UI Structure (ModelsPage.tsx)

The page is structured in `DashboardShell` with a `NeuralNetwork` background. Layout from top to bottom:

1. **Page Header** (lines 138-156): Brain icon + "Models" title + subtitle
2. **HardwareBar** (lines 158-161): Live hardware status bar at the top
3. **Loading Skeleton** (lines 164-177): Shimmer placeholders
4. **Error State** (lines 180-195): Error message with Retry button
5. **Top Picks Carousel** (lines 206-211): Top 5 recommendations, auto-rotating
6. **Workload Columns** (lines 214-217): Per-workload model groupings
7. **Catalog Table** (lines 220-223): Full model catalog with filters
8. **Installed Bar** (lines 226-238): Collapsible bar of installed models

### VRAM/RAM Monitoring — Live Usage Display

**Current state:** PARTIALLY IMPLEMENTED — static snapshot only, no live monitoring.

- `HardwareBar.tsx` (lines 10-63) renders GPU name, VRAM total, RAM used/total with a percentage bar, disk free, and CUDA/Metal badges.
- Data comes from `HardwareProfile` fetched once via `modelsApi.recommendedEnhanced()` on page load (line 50).
- **Missing:**
  - No periodic refresh of VRAM/RAM usage (fetched once at mount).
  - No live GPU utilization % or VRAM usage bar (only RAM has a bar).
  - No WebSocket-based live hardware telemetry (the `useSystemWebSocket` hook is only used for download progress, lines 106-125).
  - No VRAM usage visualization — only total VRAM is shown (line 20: `gpu.vram_gb`), not used/available.
  - Backend `/models/hardware` endpoint (line 165) calls `_detect_hardware()` which uses `psutil` — this is a snapshot, not streaming.

### API Client (models.ts)

Comprehensive — 26 methods covering:
- `list`, `recommended`, `hardware`, `health`, `metrics`
- `download`, `progress`, `cancel`, `downloadQueue`, `downloadHistory`
- `recommendedEnhanced`, `installed`, `storage`, `refreshCatalogue`
- `detail`, `getModelDetail`, `inferenceConfig`, `checkUpdates`
- `search`, `compare`, `sync`, `syncStatus`, `autocomplete`
- `usageStats`, `getUsageStats`, `delete`, `getSettings`, `updateSettings`

**Missing from frontend client but present in backend:**
- Nothing significant — the client is comprehensive.

### Backend Endpoints (models.py)

24 endpoints registered on the router:

| Method | Path | Line | Description |
|--------|------|------|-------------|
| GET | `/models` | 56 | List all catalog models |
| GET | `/models/recommended` | 125 | Hardware-appropriate recommendations |
| GET | `/models/hardware` | 165 | Detect system hardware |
| GET | `/models/health` | 173 | LLM provider health check |
| GET | `/models/metrics` | 181 | Token usage metrics |
| GET | `/models/usage/stats` | 189 | Model usage statistics |
| GET | `/models/installed` | 201 | List installed models |
| GET | `/models/search` | 268 | Search/filter models |
| POST | `/models/compare` | 324 | Compare 2-5 models |
| POST | `/models/sync` | 370 | Trigger provider sync |
| GET | `/models/sync/status` | 395 | Sync job history |
| GET | `/models/autocomplete` | 409 | Model name autocomplete |
| GET | `/models/storage` | 426 | Storage usage breakdown |
| GET | `/models/updates` | 460 | Check for model updates |
| GET | `/models/settings` | 516 | Get user model settings |
| PUT | `/models/settings` | 561 | Update user model settings |
| GET | `/models/downloads/queue` | 636 | Download queue status |
| GET | `/models/downloads/history` | 686 | Download history |
| POST | `/models/catalogue/refresh` | 720 | Force refresh catalogue |
| POST | `/models/{model_name}/download` | 734 | Start download |
| GET | `/models/{model_name}/progress` | 748 | Download progress |
| POST | `/models/{model_name}/cancel` | 758 | Cancel download |
| DELETE | `/models/{model_name}` | 768 | Delete Ollama model |
| GET | `/models/{model_id}` | 782 | Model detail with variants |
| GET | `/models/{model_id}/inference-config` | 828 | Inference config |

**All endpoints require auth** via `Depends(get_current_user)`.

### Catalog Table (CatalogTable.tsx)

**Currently shows:**
- Model name (line 116)
- Model type with icon (lines 117-128): chat, code, vision
- Parameter count (line 130)
- Size in GB (line 131)
- Fit rating: **hardcoded as "—"** (line 132)
- Download button (lines 134-141)

**What's missing from the catalog:**
1. **Fit/Score column is empty** — line 132 renders a dash. No VRAM compatibility data is passed to the catalog table.
2. **No quality_score display** — the backend provides `quality_score` per variant but the catalog lists models by base name, not variants.
3. **No download status indicator** — downloaded models show no badge or checkmark in the table.
4. **No benchmark scores** in catalog view (only in detail page).
5. **No context length** column.
6. **No provider/source info** (all are "ollama" but not shown).
7. **No description** — truncated or omitted entirely.
8. **No sorting by score, popularity, or size** — only type/size filters.

### Downloads Page

**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/app/downloads/DownloadManagerPage.tsx` (435 lines)

**Structure:**
1. Header with Download icon + title
2. Status badges (Active, Queued, Done, Failed)
3. Summary bar (Downloaded bytes, Remaining, ETA, Speed)
4. Active Downloads section with progress bars + cancel
5. Queued section with remove buttons
6. Completed section with delete buttons
7. Failed section with retry + dismiss buttons

**WebSocket integration:** Uses `useSystemWebSocket` on `/ws/models` to refresh queue on `model_progress` events (line 74-87).

**What works:** Full download lifecycle management. Real-time progress updates via WebSocket.

**What's missing:**
- No bulk operations (select all, cancel all).
- No download speed history/graph.
- No storage quota visualization.
- No download scheduling (e.g., "download at night").

---

## 2. Model Detail Page

### File Path

| File | Path | Lines |
|------|------|-------|
| Detail Page | `/home/adi/Desktop/Cortex-Workspace/frontend/app/models/[id]/ModelDetailPage.tsx` | 571 |

### UI Structure

1. **Breadcrumb**: Models > Model Name
2. **Hero Section**: Model icon, name, provider, params, license, description, tags, Download/Compare/External buttons
3. **Variant Table** (left column): Quantization, Size, VRAM, Quality %, Fit rating, TPS estimate, Download button
4. **Specifications Grid**: Parameters, Architecture, Context Length, Training Data, License, Family
5. **Performance Sidebar**: Generation Speed bar, Prompt Processing bar, VRAM Usage bar, Max Context bar
6. **Hardware Compatibility Sidebar**: GPU VRAM check, System RAM check, Disk Space check, CUDA Support check
7. **Benchmarks Sidebar**: HumanEval, MBPP, MMLU, GSM8K scores
8. **About Quantization**: Static educational text

### Issues Found

1. **Hardcoded benchmarks** (lines 318-323): All four benchmark scores are hardcoded (`85.2`, `68.4`, `72.1`, `61.3`) — not from the model's `benchmarks` field.
2. **Hardcoded training data** (line 455): `"5.5T tokens"` is static, not from the model.
3. **`model.benchmarks` is available** in the backend response (line 809) but ignored in the detail page.
4. **`"Add to Compare"` button** (line 388-391) has no onClick handler — it's non-functional.
5. **"About Quantization"** text is generic Q4_K_M description, not variant-specific.

---

## 3. Downloads Page

Covered in Section 1 above. See `DownloadManagerPage.tsx`.

---

## 4. Memory Page

### File Paths

| File | Path | Lines |
|------|------|-------|
| Main Page | `/home/adi/Desktop/Cortex-Workspace/frontend/app/memory/page.tsx` | 1310 |
| MemorySearch | `/home/adi/Desktop/Cortex-Workspace/frontend/app/memory/MemorySearch.tsx` | 86 |
| MemoryEditor | `/home/adi/Desktop/Cortex-Workspace/frontend/app/memory/MemoryEditor.tsx` | 151 |
| MemoryDetail | `/home/adi/Desktop/Cortex-Workspace/frontend/app/memory/MemoryDetail.tsx` | 83 |
| Frontend API Client | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/api/memory.ts` | 59 |
| Backend Router | `/home/adi/Desktop/Cortex-Workspace/backend/app/api/memory.py` | 193 |

### UI Structure

The page is a complex 1310-line component with three display modes:

**Header Section** (lines 459-575):
- Brain icon + "Memory" title + entry count
- View mode toggle: Graph / List / Learning
- Refresh + New Memory buttons
- Detail panel toggle
- `MemorySearch` component (search bar + semantic toggle)
- Category filter chips

**Auto-Sync Prompt** (lines 578-630):
- Banner shown when no watched paths exist
- "Sync All" and "Configure" buttons

**Active Sync Progress** (lines 633-664):
- Animated spinner + status text + progress bar
- Shows when a sync job is pending/running

**Content Area** (lines 674-1013):
1. **Graph View** (lines 706-828): SVG knowledge graph with category nodes + entry nodes, glow effects, clickable
2. **List View** (lines 831-894): Scrollable card list with category badges, tags, search scores
3. **Learning View** (lines 896-1013): Long-term memory stats, per-category breakdowns, confidence bars, reinforce/delete buttons

**Right Detail Panel** (lines 1017-1073): 384px sidebar showing selected entry details

**Sync Modal** (lines 1081-1306): Full configuration modal with:
- Default home directories (checkboxes)
- Custom directory input with live validation
- Embedding model selector with speed/description
- Exclude directories management
- Start Auto-Sync button

### Frontend API Client (memory.ts)

7 methods:
- `list` (GET `/api/v1/memory`) — pagination + category filter
- `create` (POST `/api/v1/memory`)
- `get` (GET `/api/v1/memory/{id}`)
- `update` (PUT `/api/v1/memory/{id}`)
- `delete` (DELETE `/api/v1/memory/{id}`)
- `search` (POST `/api/v1/memory/search`)
- `scanRepo` (POST `/api/v1/memory/scan-repo`)

### Backend Endpoints (memory.py)

7 endpoints:

| Method | Path | Line | Description |
|--------|------|------|-------------|
| GET | `/api/v1/memory` | 49 | List entries with pagination |
| POST | `/api/v1/memory` | 76 | Create entry with vector embedding |
| GET | `/api/v1/memory/{entry_id}` | 95 | Get single entry |
| PUT | `/api/v1/memory/{entry_id}` | 109 | Update entry + re-embed |
| DELETE | `/api/v1/memory/{entry_id}` | 132 | Delete entry + vector |
| POST | `/api/v1/memory/search` | 147 | Semantic search |
| POST | `/api/v1/memory/scan-repo` | 172 | Background repo scan |
| POST | `/api/v1/memory/bulk-embed` | 186 | Bulk embedding (extra, not in frontend client) |

**All endpoints require auth.** Ownership checks present (lines 104, 119, 141).

### Sync Visual Indication — What Works and What's Missing

**What exists:**
- Auto-sync prompt banner (line 578) with "Sync All" / "Configure" / "Dismiss"
- Active job progress bar (lines 633-664) with spinner + progress text + bar
- Sync status polled every 5 seconds (line 182-186)
- Sync jobs fetched on same interval

**What's missing:**
1. **No sync status indicator on the page header** — no persistent badge showing "Synced X min ago" or "Syncing..."
2. **No per-watched-path status** — the `syncStatus.watched_paths` data is fetched but never rendered in the main page (only checked for emptiness on line 137).
3. **No last-sync timestamp** displayed prominently — `syncStatus.last_sync` is available but not shown.
4. **No error count display** — `syncStatus.errors` is available but only rendered in the Settings page's `IndexingConfigForm`, not on the Memory page.
5. **No sync history/log** — only current jobs, no historical view of past syncs.
6. **No stop/pause button** on the active progress bar — `handleStopSync` exists (line 256) but the stop button is not rendered in the progress UI.
7. **No file-change count** — `syncStatus.pending_changes` and `syncStatus.indexed_files` are not displayed on the Memory page.

### MemoryEditor (MemoryEditor.tsx)

Modal-based editor with fields:
- Title (required)
- Content (required, textarea)
- Category (free text input — not a dropdown of valid categories)
- Source path (optional)
- Tags (comma-separated text)

**Issue:** The category field is a free-text input, but the backend validates against `VALID_CATEGORIES = ("preference", "pattern", "correction", "fact", "context", "conversation", "note", "general")` (memory.py line 16). Users can enter invalid categories and get a 422 error.

### MemoryDetail (MemoryDetail.tsx)

Modal showing:
- Category badge + tags + "embedded" badge
- Source path
- Content in a bordered box
- Created/Updated timestamps
- Delete + Edit buttons

**Issue:** Uses `window.confirm()` for delete (line 25) instead of the project's design system confirmation pattern.

---

## 5. Profile Page

### File Path

| File | Path | Lines |
|------|------|-------|
| Main Page | `/home/adi/Desktop/Cortex-Workspace/frontend/app/profile/page.tsx` | 418 |

### UI Structure

1. **Page Header** (lines 119-127): "Your profile" title + subtitle
2. **Profile Photo Card** (lines 130-167):
   - 96px circular avatar with initials fallback
   - Hover overlay with Camera icon for upload
   - Loading spinner overlay
   - Change/Upload + Remove buttons
   - File format hint (JPEG, PNG, WebP, max 2MB)
3. **Personal Information Card** (lines 169-202):
   - Full name input
   - Nickname input
   - Bio textarea (2 rows)
   - Description textarea (3 rows)
   - Error/success messages
   - Save button
4. **GitHub Card** (lines 204-247):
   - GitHub icon + connection status (green pulse dot)
   - If not connected: username + PAT inputs + "Generate a token" link + Connect button
   - If connected: Disconnect button
5. **Developer Profile Card** (lines 250-357):
   - Programming Languages: 12 preset toggles (Python, TypeScript, JS, Rust, Go, Java, C++, C#, Ruby, PHP, Swift, Kotlin)
   - Frameworks & Tools: 12 preset toggles (React, Next.js, FastAPI, Django, Flask, Docker, K8s, PostgreSQL, Redis, TensorFlow, PyTorch, Tailwind)
   - Contribution Style: 8 preset toggles (Full-stack, Backend, Frontend, DevOps, ML/AI, Security, Mobile, Data)
   - Current Projects: 3 name+description input pairs
6. **Social Links Card** (lines 360-384):
   - Twitter/X, LinkedIn, Website inputs
7. **Account Card** (lines 386-413):
   - Username, Role, User ID (read-only display)

### What Needs Redesign

1. **No visual preview of the profile** — no card showing how the profile looks to others.
2. **Hardcoded technology lists** — Languages (12), Frameworks (12), Styles (8) are all hardcoded arrays. No ability to add custom entries.
3. **No username/email change** — username is displayed read-only but cannot be edited.
4. **No password change** functionality.
5. **No 2FA/security settings**.
6. **No account deletion** on this page (it's on Settings instead).
7. **No activity/history** section showing recent actions.
8. **No "last active" timestamp**.
9. **GitHub PAT handling** — token is sent in plaintext to the backend. The backend stores it encrypted, but the frontend sends it as a plain form field. No visibility into what permissions are needed.
10. **No confirmation step** for GitHub disconnect (uses `confirm()` on line 107).
11. **Projects limited to 3** with no explanation why.
12. **No drag-and-drop** for avatar upload.
13. **No image crop/preview** before upload.

---

## 6. Settings Page

### File Paths

| File | Path | Lines |
|------|------|-------|
| Main Page | `/home/adi/Desktop/Cortex-Workspace/frontend/app/settings/page.tsx` | 276 |
| IndexingConfigForm | `/home/adi/Desktop/Cortex-Workspace/frontend/app/settings/IndexingConfigForm.tsx` | 270 |

### UI Structure

1. **Page Header** (lines 83-91): "Settings" title + "Manage your account" subtitle
2. **Account Information Card** (lines 94-136):
   - Username, Role, User ID, Storage Root (read-only)
   - "Edit Profile" button linking to `/profile`
3. **Preferences Card** (lines 138-210):
   - Accent Color: 4 color circles (cyan, purple, green, amber)
   - Font Size: Small/Medium/Large toggle
   - Sidebar: Expanded/Collapsed toggle
   - Save preferences button
4. **IndexingConfigForm** (lines 212):
   - Indexing Status: Watching, Indexed Files, Pending Changes, Errors
   - Indexing Configuration: Include/Exclude paths, patterns, max file size, sync interval, priority, follow symlinks, sync enabled
   - Preview Indexing: path input + preview stats (5-column grid)
5. **Delete Account Card** (lines 214-271):
   - Warning icon + description
   - Two-step confirmation: first click reveals password input
   - Irreversible warning banner
   - Password input + Cancel/Delete buttons

### What Settings Are Available

| Setting | Location | Line |
|---------|----------|------|
| Accent Color | Settings > Preferences | 143-163 |
| Font Size | Settings > Preferences | 167-183 |
| Sidebar Default | Settings > Preferences | 186-202 |
| Indexing Include Paths | IndexingConfigForm | 143-149 |
| Indexing Exclude Paths | IndexingConfigForm | 151-157 |
| Indexing Include Patterns | IndexingConfigForm | 160-166 |
| Indexing Exclude Patterns | IndexingConfigForm | 169-175 |
| Max File Size | IndexingConfigForm | 179-185 |
| Sync Interval | IndexingConfigForm | 187-194 |
| Indexing Priority | IndexingConfigForm | 198-205 |
| Follow Symlinks | IndexingConfigForm | 210-217 |
| Sync Enabled | IndexingConfigForm | 219-227 |

### What's Missing / Outdated

1. **No LLM/Model settings UI** — backend has `GET/PUT /models/settings` (models.py lines 516-633) for `inference_backend`, `huggingface_token`, `auto_download`, `max_concurrent_downloads`, but there's no frontend form for these settings.
2. **No notification preferences** — `notifications` table exists (migration line 170) but no settings UI.
3. **No theme/dark mode toggle** — accent color exists but no full theme switcher.
4. **No API key management** — no UI for managing tokens beyond GitHub PAT (on Profile page).
5. **No data export/import** settings.
6. **Preferences are cosmetic only** — accent color, font size, sidebar are stored in `user.preferences_json` but don't appear to be applied globally (no CSS variable updates visible).
7. **No chat/model defaults** — cannot set default model, temperature, etc.
8. **No privacy settings** — no controls for data sharing, telemetry, etc.
9. **Indexing config has no validation feedback** — errors are silently caught (line 73-77).
10. **No keyboard shortcuts** section.

---

## 7. Migration Chain Audit

### Migration Files

| File | Revision | Down Revision | Lines |
|------|----------|---------------|-------|
| `b00000000000_baseline.py` | `b00000000000` | `None` | 919 |
| `c00000000002_add_users_deleted_at_index.py` | `c00000000002` | `b00000000000` | 21 |

### Migration Chain

```
None → b00000000000 (baseline) → c00000000002 (add users.deleted_at index)
```

**Chain integrity:** ✅ VALID. The chain is linear with no broken references.

### Baseline Migration (b00000000000)

Creates 35 tables in a single consolidated migration:
1. `users`
2. `auth_events`
3. `knowledge_entries`
4. `user_storage_registry`
5. `repo_indexes`
6. `code_chunks`
7. `notifications`
8. `graph_nodes`
9. `graph_edges`
10. `indexed_files`
11. `agents`
12. `agent_runs`
13. `agent_steps`
14. `agent_feedback`
15. `indexing_configs`
16. `conversations`
17. `conversation_messages`
18. `documents`
19. `document_chunks`
20. `embedding_cache`
21. `model_catalog`
22. `model_variants`
23. `model_downloads`
24. `model_usage`
25. `providers`
26. `capabilities`
27. `provider_models`
28. `quantizations`
29. `hardware_profiles`
30. `model_statistics`
31. `sync_jobs`
32. `long_term_memories`
33. `path_index`
34. `sync_states`
35. `user_model_settings`

Plus: 3 foreign key back-fills, 2 GIN full-text search indexes, 1 ENUM type.

**Note:** The docstring says "replaces all 27 prior migrations (a00000000001 ... z00000000025)" — this is a clean consolidation.

### Second Migration (c00000000002)

Adds `ix_users_deleted_at` index on `users.deleted_at` for soft-delete query performance.

**Both `upgrade()` and `downgrade()` are properly defined** in both migrations. ✅

### Potential Issues

1. **No revision `c00000000001`** — the chain jumps from `b00000000000` to `c00000000002`. This is valid in Alembic (revision IDs don't need to be sequential numbers), but it's unusual and could cause confusion if someone expects sequential numbering.
2. **No migration for `model_variants` missing columns** — if `architecture`, `quantization_bits`, `bits_per_param`, `quality_multiplier`, `speed_multiplier` were added later, they're already in the baseline. No issue.
3. **Downgrade order** (lines 876-919): Tables are dropped in reverse dependency order. The `providers` table is dropped after `model_variants` which has FK to it — this will fail because `model_variants` is dropped first (line 889), then `providers` (line 896). Wait — actually `model_variants` has FK to `providers`, so `providers` must be dropped AFTER `model_variants`. The downgrade order drops `model_variants` (line 889) before `providers` (line 896), which is correct. ✅

---

## Summary of Critical Findings

### Models Page
| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | Medium | Hardware status is a one-shot snapshot, not live | ModelsPage.tsx:50, HardwareBar.tsx |
| 2 | Medium | Catalog "Fit" column is always "—" | CatalogTable.tsx:132 |
| 3 | Low | No VRAM usage visualization in HardwareBar | HardwareBar.tsx |
| 4 | Medium | Model detail benchmarks are hardcoded | ModelDetailPage.tsx:318-323 |
| 5 | Low | "Add to Compare" button is non-functional | ModelDetailPage.tsx:388-391 |

### Memory Page
| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | Medium | No sync status indicator in header | page.tsx |
| 2 | Low | Watched path status not displayed | page.tsx:137 |
| 3 | Low | Stop button not rendered in active sync UI | page.tsx:256 vs 633-664 |
| 4 | Medium | Category field is free-text but backend validates | MemoryEditor.tsx:110-116 |
| 5 | Low | Delete uses `window.confirm()` | MemoryDetail.tsx:25 |

### Profile Page
| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | Low | No profile preview card | page.tsx |
| 2 | Low | Hardcoded tech lists, no custom entries | page.tsx:258-323 |
| 3 | Low | No password change UI | page.tsx |

### Settings Page
| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | High | No UI for LLM/model settings (backend exists) | page.tsx vs models.py:516-633 |
| 2 | Medium | Preferences may not be applied (no CSS integration visible) | page.tsx:143-202 |
| 3 | Low | No notification preferences | page.tsx |

### Migrations
| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | Info | Revision ID gap (b→c00000000002, no c00000000001) | migrations/versions/ |
| — | ✅ | Chain integrity valid | — |
| — | ✅ | Both upgrade/downgrade defined | — |
