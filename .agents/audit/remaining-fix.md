# Remaining Fixes & Recommendations

> Last updated: 2026-06-22
> Purpose: Single source of truth for pending work across Cortex

---

## ✅ All Backend / Security / DB / Quality / Architecture Items — FIXED

- P0/P1 Critical: All 6 items fixed (agent self-approval, token store docs, SyncStatusResponse, repo path validation, metrics auth, error sanitization)
- Security: All 12 items fixed (WS header tokens, password validation, vault re-encryption, cache docs, SECRET_KEY rotation, Redis password, repo owner filter, CSP/Cache-Control/Permissions-Policy headers, x-xss-protection removed, DB credentials removed)
- DB: All 14 items fixed (server_default, CHECK constraints, GIN simple config, if_exists guards, FK indexes, nullable constraints, unique constraints, model exports, TTL enforcement, TIMESTAMPTZ consistency, model_variants consolidation, engine pool settings)
- Quality: All 14 items fixed (LLMHealthResponse/LLMMetricsResponse populated, endpoints have response_model=, models.py split, DateTime consistency, server_default audit, parameter_count aligned, LLMManager session param, thread-safe singletons, circuit breaker, deep health check, SECRET_KEY generation, typed AgentFeedback, GIN simple config, is_stale service)
- Architecture Cleanup: All 9 items fixed (dead files deleted, embed_with_cache removed, sync.py cleaned, models.py split, domain API modules)
- Contract Mismatches: All 6 HIGH items fixed (installed shape, downloadHistory shape, search result shape, recommended uses recommendedEnhanced, compare extra field ignored, usageStats endpoint correct)

---

## UI/UX — Pending (Future Work)

### HIGH Priority — All Fixed

- **#1 WebSocket processes data** ✅ — Added `collect_processes()` in `ws_system.py` (runs every 5s)
- **#2 AgentChat SSE streaming** ✅ — Switched to `agentApi.streamRun()` with abort support + fallback
- **#3 LLM/model settings UI** ✅ — Built `LLMSettingsForm.tsx` with backend selector, HF token, auto-download toggle

### MEDIUM Priority — All Fixed

| # | Issue | Status |
|---|-------|--------|
| 4 | Activity tab shows backend logs | ✅ Enhanced with level-based icons, color coding, module info |
| 5 | Insights tab is static cards | ✅ Added agent runs count, replaced hardcoded cards with real links |
| 6 | Memory page monolith (1310+ lines) | ✅ Extracted graph view → MemoryGraphView.tsx, learning view → MemoryLearningView.tsx |
| 7 | MemoryEditor category free-text | ✅ Replaced with <select> dropdown of 6 valid categories |
| 8 | Search orphaned components | ✅ Deleted SearchFilters.tsx, SearchResults.tsx, GraphView.tsx |
| 9 | No pagination in search results | ✅ Added cursor-based Load More button |
| 10 | No model/tool selection during agent creation | ✅ Already implemented (AgentEditor has model dropdown + tools selector) |
| 11 | No feedback UI for agent runs | ✅ Added thumbs up/down on last assistant message via agentApi.addFeedback() |
| 12 | No conversation renaming | ✅ Added PATCH /conversations/{id}/title endpoint + frontend conversationsApi.rename() |
| 13 | No stop/cancel button for streaming | ✅ Added visible stop button in AgentChat using abortRef |
| 14 | Model detail benchmarks hardcoded | ✅ Uses model.benchmarks from backend (typed optional field on ModelCatalogEntry) |
| 15 | "Add to Compare" button non-functional | ✅ Wired to sessionStorage + /models/compare with try/catch |
| 16 | Catalog "Fit" column always "—" | ✅ Computes VRAM fit from hardware_requirements.min_vram_gb vs gpu.vram_available_gb |
| 17 | HardwareBar only static snapshot | ✅ Already implemented (accepts liveMetrics prop from WebSocket) |
| 18 | No sync status indicator on memory page | ✅ Added sync badge in header showing indexed file count or syncing animation |
| 10 | No model/tool selection during agent creation | Add model dropdown + tools selector |
| 11 | No feedback UI for agent runs | Add thumbs up/down on responses |
| 12 | No conversation renaming | Add inline edit on title |
| 13 | No stop/cancel button for streaming | Add abort controller support |
| 14 | Model detail benchmarks hardcoded | Use `model.benchmarks` from backend |
| 15 | "Add to Compare" button non-functional | Wire to `/models/compare` endpoint |
| 16 | Catalog "Fit" column always "—" | Pass VRAM compatibility data |
| 17 | HardwareBar only static snapshot | Add WebSocket-based live telemetry |
| 18 | No sync status indicator on memory page | Add sync badge in header |

### LOW Priority

| # | Issue | What to do |
|---|-------|------------|
| 19 | Chat conversation list only title | Add last message preview |
| 20 | Accent color saved but not applied globally | Wire to CSS variables |
| 21 | Notifications button shows "coming soon" | Build notification panel |
| 22 | Delete uses `window.confirm()` | Replace with design system modal |
| 23 | No tests for Landing/Downloads pages | Add test coverage |
| 24 | Error boundaries duplicated (3 files) | Extract to shared component |
| 25 | Search page missing auth redirect | Add `useAuth()` pattern |

---

## Ollama Integration — Remaining

| # | Item | What to do |
|---|------|------------|
| 1 | `last_used` / `usage_count` tracking | Add from Ollama or usage tracker |
| 2 | Frontend periodic polling for installed models | Add WS subscription or polling |
