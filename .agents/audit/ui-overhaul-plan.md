# Cortex UI/UX Overhaul — Implementation Plan

**Created:** 2026-06-22
**Status:** PLANNING
**Scope:** Dashboard, Search, Agents, Chat, Models, Memory, Profile, Settings pages

---

## Task Inventory

### 1. Dashboard Page (8 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 1.1 | Add live VRAM usage ring to dashboard | HIGH | LOW | Backend already returns `memory_used_mb`/`memory_total_mb` via `get_gpu_info()`. Add a 4th MetricRing for VRAM. Currently only shows GPU name as text. |
| 1.2 | Fix WebSocket authentication | HIGH | LOW | Frontend `useSystemWebSocket.ts:82` connects without `?token=` param. Backend `ws_system.py:61-70` requires it and closes with 4001. WS data silently fails, HTTP fallback masks it. |
| 1.3 | Include process data in WebSocket stream | HIGH | LOW | `ws_system.py:collect_metrics()` (line 29-41) does NOT include `processes` in payload. Processes tab only updates via 30s HTTP fallback, goes stale after WS connects. |
| 1.4 | Fix Processes tab CPU >100% | HIGH | LOW | First process shows unrealistic CPU values. Check `system_info.py` `get_process_list()` — likely summing across cores without normalizing. |
| 1.5 | Upgrade dashboard animations | MEDIUM | LOW | Currently uses framer-motion. Add: animated number counters on metric rings, staggered card entrance, pulse effect on live data updates, smooth tab transitions. |
| 1.6 | Add live Activity logs (not backend logs) | MEDIUM | MEDIUM | Activity tab shows Python logging records (500 buffer), not user-facing activity. Need to create a user activity event system or repurpose existing data. |
| 1.7 | Enhance Insights tab | MEDIUM | LOW | Currently 4 static cards (vault, memory, agents, member since). Add: usage trends (tokens over time), model performance stats, storage breakdown chart, system health summary. |
| 1.8 | Add VRAM usage bar to GPU card | MEDIUM | LOW | GPU info card shows name only. Add progress bar showing VRAM used/total with percentage. |

### 2. Search Page (6 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 2.1 | Integrate orphaned SearchFilters component | HIGH | LOW | `SearchFilters.tsx` (107 lines) is built but never imported. Wire it into `page.tsx` to enable repo_id, node_type, language filters. |
| 2.2 | Fix search filter params (GET endpoint) | HIGH | LOW | Backend GET endpoint (`unified_search_get`) ignores `node_type`/`language`. Frontend always uses GET. Either add params to GET handler or switch frontend to POST. |
| 2.3 | Integrate orphaned SearchResults component | MEDIUM | LOW | `SearchResults.tsx` (106 lines) has richer rendering (score badges, type pills) but page uses simpler inline rendering. Replace inline with the component. |
| 2.4 | Add pagination (infinite scroll or "Load more") | MEDIUM | LOW | Backend supports `next_cursor`/`has_more`. Frontend makes single request with `max_results: 20`. Add "Load more" button or infinite scroll. |
| 2.5 | Add search debounce (300ms) | LOW | LOW | Currently only triggers on Enter/button. Add debounced search-as-you-type for better UX. |
| 2.6 | Fix result links (non-functional ExternalLink) | LOW | LOW | Results show ExternalLink icon but no `href`/click handler. Add click to open file in editor or navigate to repo. |

### 3. Agents Page (6 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 3.1 | Replace polling with SSE streaming in AgentChat | HIGH | MEDIUM | Currently uses 2-second polling. Backend has SSE endpoint `/agents/runs/{run_id}/stream`. Switch to streaming for real-time responses. |
| 3.2 | Add agent creation with model/tools selection | HIGH | LOW | Create modal only has name/description/system_prompt. Model and tools can only be set in Edit. Add model dropdown and tools selector to Create. |
| 3.3 | Add feedback UI | MEDIUM | LOW | Backend supports create/list feedback. Add thumbs up/down buttons on agent responses with optional comment. |
| 3.4 | Add agent metrics dashboard | MEDIUM | LOW | Backend returns success_rate, avg_duration, total_runs. Add a stats summary card at top of agents page. |
| 3.5 | Improve agent card design | MEDIUM | LOW | Add: last run timestamp, success rate badge, quick actions (run, edit, delete). |
| 3.6 | Add agent run history timeline | LOW | LOW | Show a timeline of past runs with status, duration, and output preview. |

### 4. Chat Page (8 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 4.1 | Complete UI redesign | HIGH | HIGH | Current UI is basic. Redesign with: proper message bubbles, code syntax highlighting, markdown rendering, copy button, streaming indicator, thinking/reasoning display. |
| 4.2 | Add conversation renaming | MEDIUM | LOW | Users can't rename conversations. Add inline edit on title. |
| 4.3 | Add message actions (copy, regenerate, edit) | MEDIUM | LOW | Add hover actions on each message: copy content, regenerate response, edit user message. |
| 4.4 | Add stop/cancel button for streaming | MEDIUM | LOW | No way to stop a streaming response. Add abort controller support. |
| 4.5 | Add conversation sidebar improvements | MEDIUM | LOW | Current sidebar shows only title. Add: last message preview, message count, model used badge. |
| 4.6 | Create dedicated conversationApi client | LOW | LOW | All API calls are inline raw `api.get`/`api.post`. Extract to `shared/api/conversation.ts` for consistency. |
| 4.7 | Add model selector in chat | LOW | LOW | No way to choose which model to use for a conversation. Add model dropdown in chat header. |
| 4.8 | Add message search within conversation | LOW | LOW | No way to search within a conversation. Add search bar in chat header. |

### 5. Models Page (6 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 5.1 | Add live VRAM/RAM usage at top | HIGH | LOW | HardwareBar only shows static snapshot. Add WebSocket-based live telemetry or 5s polling for VRAM/RAM usage. |
| 5.2 | Fix catalog table (show all model data) | HIGH | LOW | "Fit" column always shows "—". Add: quality score, parameter count, download status, size display. |
| 5.3 | Add model detail benchmarks from actual data | MEDIUM | LOW | Benchmarks are hardcoded. Use `model.benchmarks` field from backend. |
| 5.4 | Fix "Add to Compare" button | MEDIUM | LOW | Compare button is non-functional. Wire to `/models/compare` endpoint. |
| 5.5 | Update downloads page with live progress | MEDIUM | LOW | Add real-time download progress bars, speed, ETA using WebSocket. |
| 5.6 | Add VRAM usage ring to HardwareBar | MEDIUM | LOW | Only RAM has a usage bar. Add VRAM usage bar with percentage. |

### 6. Memory Page (4 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 6.1 | Add sync status visual indicator | HIGH | LOW | No visual feedback that sync is happening. Add: sync badge in header, per-path status, spinner during sync, last-sync timestamp. |
| 6.2 | Fix MemoryEditor category validation | MEDIUM | LOW | Category is free-text but backend validates against 8 fixed categories. Replace with dropdown/select. |
| 6.3 | Replace window.confirm with design system modal | LOW | LOW | MemoryDetail uses `window.confirm()`. Replace with proper confirmation modal. |
| 6.4 | Add memory search/filter | LOW | LOW | No way to search within memories. Add search bar with category filter. |

### 7. Profile Page (3 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 7.1 | UI redesign with profile preview | MEDIUM | LOW | Add: live preview card, cover photo, activity summary, better layout. |
| 7.2 | Add password change functionality | MEDIUM | LOW | No way to change password from profile page. Add password change form. |
| 7.3 | Improve developer profile section | LOW | LOW | Hardcoded language/framework lists. Make them dynamic and searchable. |

### 8. Settings Page (4 tasks)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 8.1 | Add model inference settings UI | HIGH | LOW | Backend has `GET/PUT /models/settings` for inference_backend, HF token, auto_download, max_concurrent_downloads — but NO frontend UI exists. |
| 8.2 | Add notification preferences | MEDIUM | LOW | No notification settings UI. |
| 8.3 | Add theme/appearance settings | MEDIUM | LOW | Accent color is saved but not applied globally. Add proper theme settings. |
| 8.4 | Add API key management | LOW | LOW | No UI for managing API keys or tokens. |

### 9. Migration Fix (1 task)

| # | Task | Priority | Risk | Details |
|---|------|----------|------|---------|
| 9.1 | Fix migration chain (missing c00000000001) | HIGH | MEDIUM | `c00000000002` references `c00000000001` as down_revision but the actual baseline is `b00000000000`. Fix the revision chain. |

---

## Implementation Order

### Phase 1: Critical Fixes (Tasks 1.2, 1.3, 1.4, 2.2, 5.2, 9.1)
WebSocket auth, process data, CPU fix, search filters, catalog data, migration fix.
**Risk: LOW-MEDIUM | Impact: HIGH**

### Phase 2: Live Data (Tasks 1.1, 1.8, 5.1, 5.6, 6.1)
VRAM monitoring on dashboard and models page, memory sync indicator.
**Risk: LOW | Impact: HIGH**

### Phase 3: Search & Agents (Tasks 2.1, 2.3, 2.4, 3.1, 3.2)
Wire orphaned components, pagination, SSE streaming, agent creation.
**Risk: LOW-MEDIUM | Impact: HIGH**

### Phase 4: Chat Redesign (Tasks 4.1, 4.2, 4.3, 4.4, 4.5)
Complete chat UI overhaul with message bubbles, streaming, actions.
**Risk: HIGH | Impact: HIGH**

### Phase 5: Models & Settings (Tasks 5.3, 5.4, 5.5, 8.1)
Model detail fixes, compare button, download progress, settings UI.
**Risk: LOW | Impact: MEDIUM**

### Phase 6: Dashboard Enhancements (Tasks 1.5, 1.6, 1.7)
Animations, activity events, insights tab.
**Risk: LOW | Impact: MEDIUM**

### Phase 7: Profile & Memory (Tasks 6.2, 6.3, 7.1, 7.2, 8.2, 8.3)
Profile redesign, memory fixes, settings additions.
**Risk: LOW | Impact: LOW-MEDIUM**

### Phase 8: Polish (Tasks 2.5, 2.6, 3.3, 3.4, 3.5, 3.6, 4.6, 4.7, 4.8, 6.4, 7.3, 8.4)
Debouncing, links, feedback, metrics, search, minor improvements.
**Risk: LOW | Impact: LOW**

---

## Key Files Reference

### Dashboard
- `frontend/app/app/page.tsx` (318 lines)
- `frontend/app/app/loading.tsx`, `error.tsx`
- `frontend/src/shared/ui/MetricRing.tsx` (86 lines)
- `frontend/src/shared/ui/TabGroup.tsx` (98 lines)
- `frontend/src/shared/components/SyncStatus.tsx` (615 lines)
- `backend/app/core/system_info.py` — GPU/VRAM data source
- `backend/app/api/v1/system.py` — System metrics endpoint
- `backend/app/api/ws_system.py` — WebSocket system data

### Search
- `frontend/app/search/page.tsx` (198 lines)
- `frontend/app/search/SearchResults.tsx` (106 lines) — ORPHANED
- `frontend/app/search/SearchFilters.tsx` (107 lines) — ORPHANED
- `frontend/app/search/GraphView.tsx` (213 lines) — ORPHANED
- `frontend/src/shared/api/search.ts` (59 lines)
- `backend/app/api/v1/search.py` (236 lines)

### Agents
- `frontend/app/agents/page.tsx` (334 lines)
- `frontend/app/agents/AgentEditor.tsx` (208 lines)
- `frontend/app/agents/AgentChat.tsx` (300 lines)
- `frontend/src/shared/api/agent.ts` (118 lines)
- `backend/app/api/v1/agents.py` (497 lines)

### Chat
- `frontend/app/chat/page.tsx` (374 lines)
- `backend/app/api/v1/conversations.py` (220 lines)

### Models
- `frontend/app/models/ModelsPage.tsx` (244 lines)
- `frontend/app/models/components/HardwareBar.tsx` (64 lines)
- `frontend/app/models/components/CatalogTable.tsx` (170 lines)
- `frontend/app/models/components/TopPicksCarousel.tsx` (120 lines)
- `frontend/app/models/components/InstalledBar.tsx` (83 lines)
- `frontend/src/shared/api/models.ts` (178 lines)
- `backend/app/api/v1/models.py` (1001 lines)

### Memory
- `frontend/app/memory/page.tsx` (1310 lines)
- `backend/app/api/memory.py`

### Profile
- `frontend/app/profile/page.tsx` (418 lines)

### Settings
- `frontend/app/settings/page.tsx` (276 lines)
- `frontend/app/settings/PreferencesPage.tsx` (270 lines)

---

## Design System Reference

- **Theme:** Warm Neural Dark (OLED black backgrounds)
- **Animations:** framer-motion (spring physics)
- **Components:** Radix UI primitives
- **Background:** NeuralNetwork canvas (Three.js)
- **Cards:** Glass morphism with glow effects
- **Colors:** Neural Blue (#3B82F6), Synapse Green (#10B981), Cortex Purple (#8B5CF6)
- **Typography:** Inter (body), JetBrains Mono (code)

---

*This document captures all tasks from the user's feedback. Review before implementing.*
