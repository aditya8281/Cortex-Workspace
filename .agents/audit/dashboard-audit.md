# Cortex Dashboard Page — Comprehensive Audit Report

**Date:** 2026-06-22  
**Scope:** `/frontend/app/app/page.tsx` and all supporting files  

---

## 1. Dashboard Main Page

**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.tsx` (318 lines)

### Current Implementation
- A `"use client"` Next.js page component at route `/app`
- Shows a welcome hero with user avatar, name, role badge, and `SyncStatus` component
- Displays three `MetricRing` components (CPU, RAM, Disk) and a GPU info card
- Three tabs: Activity, Processes, Insights (via `TabGroup`/`TabPanel`)
- Uses `DashboardShell` layout wrapper and `NeuralNetwork` canvas background
- Data comes from two sources: WebSocket (live) and HTTP cold-start/fallback

### Data Flow
| Data | Source | Endpoint |
|------|--------|----------|
| System metrics (CPU, RAM, GPU, Disk, Processes) | WebSocket every 2s | `ws://.../ws/system` |
| System metrics (HTTP fallback) | `apiSystemMetrics()` | `GET /api/v1/system/metrics` |
| System logs (live) | WebSocket every 6s | `ws://.../ws/system` |
| System logs (HTTP fallback) | `apiSystemLogs(15)` | `GET /api/v1/system/logs?limit=15` |
| Memory count | `memoryApi.list({ limit: 1 })` | `GET /api/v1/memory?limit=1` |
| Agent count | `agentApi.list()` | `GET /api/v1/agents` |
| User profile | `useAuth()` context | Client-side |

### Supporting Files
| File | Path |
|------|------|
| Loading state | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/loading.tsx` (10 lines) |
| Error boundary | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/error.tsx` (28 lines) |
| Test file | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.test.tsx` (145 lines) |

---

## 2. Dashboard Components

### 2.1 DashboardShell
**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/layout/DashboardShell.tsx` (601 lines)

- Full layout wrapper with sidebar, header, mobile nav
- Desktop sidebar with Work/You nav groups + Vault/Memory status indicators
- Tablet overlay sidebar with AnimatePresence
- Mobile bottom tab bar
- Header with search, notifications bell, user dropdown
- Sidebar active indicator uses `motion.div` with `layoutId="sidebar-active"` (spring animation)
- Fetches vault status, memory count, notification count on mount

### 2.2 MetricRing
**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/MetricRing.tsx` (86 lines)

- SVG-based circular progress indicator
- Animates value from 0 to target over 1.5s using `requestAnimationFrame` + cubic easing
- Uses `motion.circle` from framer-motion for stroke animation
- Accepts `label`, `value`, `color`, `size`, `max`, `unit`

### 2.3 TabGroup / TabPanel
**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/TabGroup.tsx` (98 lines)

- Tab system using React Context (`TabContext`)
- Active tab indicator: `motion.div` with `layoutId="tab-indicator"` (spring, damping 30, stiffness 300)
- Tab panels: `motion.div` with opacity fade (0.2s)
- Tabs: Activity, Processes, Insights

### 2.4 NeuralNetwork
**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/NeuralNetwork.tsx` (479 lines)

- Full-screen canvas-based neural network animation
- Three intensity levels: low (30 neurons), medium (50), high (80)
- Features: hub/regular neurons, connections, signal bursts with trail effects, chain propagation
- Respects `prefers-reduced-motion` (shows static gradient instead)
- Uses seeded random for deterministic layout
- Runs via `requestAnimationFrame` loop

### 2.5 Card
**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/Card.tsx` (49 lines)

- Styled div with `hover`, `glass`, `gradient`, `glow` variants
- CSS transitions for hover lift, shadow glow

### 2.6 SyncStatus
**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/components/SyncStatus.tsx` (615 lines)

- Shows watched paths, pending changes, indexing progress
- Polls `/api/v1/sync/status` and `/api/v1/sync/jobs` every 5s
- Full settings modal for configuring auto-sync paths, embedding models, exclude dirs
- Embeds a `SyncSettingsModal` component inline

---

## 3. VRAM Usage Monitoring

### Current Status: **NOT monitored on the dashboard**

**Backend `get_gpu_info()`:**
- **File:** `/home/adi/Desktop/Cortex-Workspace/backend/app/core/system_info.py` (lines 86-155)
- Queries `nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu`
- Returns: `memory_total_mb`, `memory_used_mb`, `utilization_gpu`
- **Does NOT return `vram_available_gb`** — only raw MB values

**Backend `SystemMetricsResponse` schema:**
- **File:** `/home/adi/Desktop/Cortex-Workspace/backend/app/schemas/system.py` (lines 16-27)
- Includes: `gpu_name`, `gpu_type`, `gpu_percent`
- **Missing: `vram_total_gb`, `vram_used_gb`, `vram_percent`** — VRAM fields are not in the response schema

**Frontend `SystemMetrics` type:**
- **File:** `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/types.ts` (lines 183-195)
- Includes: `gpu_name`, `gpu_type`, `gpu_percent`
- **Missing: no VRAM fields in the type definition**

**Dashboard GPU card:**
- **File:** `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.tsx` (lines 170-174)
- Only shows `gpu_name` as text — no VRAM usage ring, no VRAM percentage

**VRAM exists elsewhere:**
- Model detail pages extensively use `vram_required_gb`, `vram_available_gb`, `vram_usage_gb` for model fitting
- Database schema has `vram_gb`, `vram_required_gb`, `recommended_vram_gb`, `average_vram_usage_gb`
- Hardware detection in `backend/app/services/hardware.py` calculates `vram_available_gb` but this is NOT exposed via the system metrics API

### What's Missing
1. Backend: `get_gpu_info()` does not return `memory.used` as a percentage or GB
2. Backend: `SystemMetricsResponse` schema has no VRAM fields
3. Backend: `collect_metrics()` in `ws_system.py` does not include VRAM data
4. Frontend: `SystemMetrics` type has no VRAM fields
5. Frontend: Dashboard has no VRAM metric ring or indicator

---

## 4. Activity Tab

**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.tsx` (lines 186-211)

### Current Implementation
- Renders `recentActivity` array (type `SystemLog[]`)
- Each item shows: bot icon, `item.message`, `item.timestamp` formatted as locale time
- Empty state: "No recent activity. Start by searching, creating agents, or adding memories."

### Data Source: **LIVE data**
- WebSocket pushes logs every ~6 seconds (`ws_system.py` line 81: `tick % 3 == 1`)
- HTTP fallback polls every 30 seconds when WS is disconnected
- Cold-start HTTP fetch on mount

### Backend Source
- **File:** `/home/adi/Desktop/Cortex-Workspace/backend/app/core/logging.py` (lines 39-55, 98-100)
- `BufferedLogHandler` captures Python `logging` records into an in-memory `deque(maxlen=500)`
- `get_recent_logs(limit)` returns the last N entries from the buffer
- Log entries include: `timestamp`, `level`, `logger`, `message`, `request_id`, `module`, `pathname`, `lineno`

### Backend Endpoints
| Endpoint | File | Line |
|----------|------|------|
| `GET /api/v1/system/logs?limit=N` | `backend/app/api/v1/system.py` | 63-70 |
| `WS /ws/system` (type: "logs") | `backend/app/api/v1/ws_system.py` | 47-54, 80-83 |

### What's Broken / Missing
- **Log level filtering not available** — no UI to filter by log level (info/warning/error)
- **No log detail view** — clicking a log entry does nothing
- **Logger/module names not shown** — only message and timestamp displayed
- **No timestamp relative formatting** — uses `toLocaleTimeString()` which loses date info for multi-day logs
- **Buffer is in-memory only** — 500 entries max, lost on server restart
- **No search/filter** — cannot search through activity logs

---

## 5. Processes Tab

**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.tsx` (lines 214-264)

### Current Implementation
- HTML table showing top 20 processes
- Columns: Name, PID, CPU%, Memory%, Status
- CPU > 50% gets `text-warning` (orange) styling
- Status badge: green for "running", muted for "sleeping"
- Process data comes from `metrics.processes` (same WebSocket/HTTP flow as system metrics)

### Data Source
- **Backend `_get_top_processes(n=20)`:**
  - **File:** `/home/adi/Desktop/Cortex-Workspace/backend/app/api/v1/system.py` (lines 17-35)
  - Uses `psutil.process_iter()` to get all processes
  - Collects: `pid`, `name`, `cpu_percent`, `memory_percent`, `status`
  - Sorts by CPU descending, returns top 20
  - Status is simplified: `psutil.STATUS_RUNNING` -> "running", everything else -> "sleeping"

- **WebSocket metrics include processes:**
  - **File:** `/home/adi/Desktop/Cortex-Workspace/backend/app/api/v1/ws_system.py` (lines 21-41)
  - **BUG:** `collect_metrics()` does NOT include `processes` field — only HTTP endpoint does
  - The HTTP endpoint includes `processes` (system.py line 59), but WebSocket does not (ws_system.py line 29-41)

### Backend Endpoints
| Endpoint | File | Line |
|----------|------|------|
| `GET /api/v1/system/metrics` (includes processes) | `backend/app/api/v1/system.py` | 38-60 |
| `WS /ws/system` (does NOT include processes) | `backend/app/api/v1/ws_system.py` | 21-41 |

### What's Broken / Missing
1. **WebSocket does NOT push process data** — `collect_metrics()` in `ws_system.py` omits `processes` field, so processes are only populated via the HTTP cold-start/fallback. After WS connects, processes go stale.
2. **No auto-refresh of processes** — HTTP fallback is every 30s, but processes are embedded in the metrics response, not a separate endpoint
3. **No sorting/pagination** — only top 20, no way to sort by memory or search
4. **Process details not available** — no way to see command line, threads, open files
5. **Memory shows percentage only** — no absolute MB/GB value shown
6. **Type mismatch** — frontend `SystemProcess` type (types.ts line 175) matches backend schema, but process data only comes from HTTP, not WS

---

## 6. Insights Tab

**File:** `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.tsx` (lines 266-313)

### Current Implementation
A 4-card grid showing:
1. **Vault** — HardDrive icon, "Active" text (hardcoded), links to `/vault`
2. **Memories** — Brain icon, shows `memoryCount` or "—", links to `/memory`
3. **Agents** — Bot icon, shows `agentCount` or "—", no link (static card)
4. **Member Since** — Clock icon, shows `user.created_at` formatted as date

### Data Source
- `memoryCount`: fetched via `memoryApi.list({ limit: 1 })` on mount (line 113)
- `agentCount`: fetched via `agentApi.list()` on mount (lines 114-117)
- `user.created_at`: from auth context

### Backend Endpoints
| Endpoint | File | Line |
|----------|------|------|
| `GET /api/v1/memory?limit=1` | `frontend/src/shared/api/memory.ts` | 9-16 |
| `GET /api/v1/agents` | `frontend/src/shared/api/agent.ts` | 10-18 |

### What's Broken / Missing
1. **Vault card is static** — always says "Active" regardless of vault lock state (DashboardShell already fetches vault locked status)
2. **Agent count card has no link** — Vault and Memory cards link out, but Agents does not
3. **No real insights** — this tab is just summary cards, not actual "insights" (no usage trends, no system health summary, no AI-generated insights)
4. **Data is fetched once** — counts do not update if you create a memory or agent elsewhere
5. **No error states** — if API calls fail, shows "—" forever with no retry

---

## 7. Animations

### Animation Library
**framer-motion** — used across 42 files in the frontend (found via grep)

### Dashboard-Specific Animations

| Component | Animation | File | Lines |
|-----------|-----------|------|-------|
| Hero welcome | `motion.div` fade-up (opacity 0->1, y 8->0, 0.5s ease) | `page.tsx` | 127-131 |
| MetricRing SVG | `motion.circle` stroke dash animation (1.5s easeOut) | `MetricRing.tsx` | 59-74 |
| MetricRing number | Custom `requestAnimationFrame` counter (1.5s cubic ease) | `MetricRing.tsx` | 34-45 |
| Tab indicator | `motion.div` with `layoutId="tab-indicator"` (spring, damping 30, stiffness 300) | `TabGroup.tsx` | 59-63 |
| Tab panel | `motion.div` opacity fade (0.2s) | `TabGroup.tsx` | 89-97 |
| NeuralNetwork | Full canvas animation: drifting neurons, signal bursts, trail effects | `NeuralNetwork.tsx` | entire file |
| Sidebar active | `motion.div` with `layoutId="sidebar-active"` (spring, damping 25, stiffness 300) | `DashboardShell.tsx` | 160-166 |
| Dashboard loading | CSS `animate-spin` on spinner | `loading.tsx` | 5 |

### Animation Quality Assessment
- **Good:** MetricRing has smooth counter + SVG animation, NeuralNetwork is sophisticated
- **Missing:** No stagger animation on the tab content cards, no entrance animation for process rows, no skeleton loading states for metrics
- **Performance:** NeuralNetwork runs at full viewport size (window.innerWidth x Height) regardless of actual display area

---

## 8. Backend API Endpoints Summary

### Registered at App Level (not under /api/v1/)
| Endpoint | Method | File | Line |
|----------|--------|------|------|
| `/ws/system` | WebSocket | `backend/app/api/v1/ws_system.py` | 60 |
| (registered in main.py) | | `backend/app/main.py` | 213 |

### Registered Under /api/v1/
| Endpoint | Method | File | Line |
|----------|--------|------|------|
| `/api/v1/system/metrics` | GET | `backend/app/api/v1/system.py` | 38 |
| `/api/v1/system/logs` | GET | `backend/app/api/v1/system.py` | 63 |
| `/api/v1/memory?limit=1` | GET | (memory router) | — |
| `/api/v1/agents` | GET | (agents router) | — |

---

## 9. Frontend API Clients

| Client | File | Dashboard Usage |
|--------|------|-----------------|
| `apiSystemMetrics()` | `frontend/src/shared/auth/cortexApi.ts` (line 506) | HTTP cold-start + WS fallback |
| `apiSystemLogs(limit)` | `frontend/src/shared/auth/cortexApi.ts` (line 510) | HTTP cold-start + WS fallback |
| `memoryApi.list()` | `frontend/src/shared/api/memory.ts` (line 9) | Insight card count |
| `agentApi.list()` | `frontend/src/shared/api/agent.ts` (line 10) | Insight card count |
| `useSystemWebSocket` | `frontend/src/shared/hooks/useSystemWebSocket.ts` (line 32) | Live metrics + logs |

**Note:** There is NO dedicated dashboard API client in `frontend/src/shared/api/`. Dashboard data is fetched via `cortexApi.ts` (system endpoints) and domain-specific API clients (memory, agents).

---

## 10. Key Issues Summary

### Critical Bugs
1. **WebSocket missing processes** — `ws_system.py:collect_metrics()` does not include `processes` in its payload (lines 29-41), so processes only update via 30s HTTP fallback. After initial WS connection, process data goes stale.

### Major Missing Features
2. **No VRAM monitoring on dashboard** — GPU data exists in the system (`nvidia-smi`) and is used extensively in model pages, but the dashboard only shows GPU name as text. No VRAM usage ring, no VRAM percentage, no VRAM bar.
3. **Activity tab shows server logs, not user activity** — Displays Python logging records (backend internal logs), not user actions like "searched for X" or "created agent Y".
4. **Insights tab is not insightful** — Just 4 static summary cards with no trends, no charts, no actionable information.

### Minor Issues
5. **No process sorting/search** in the Processes tab
6. **No log level filtering** in the Activity tab
7. **Insight counts are stale** — fetched once on mount, never refreshed
8. **Vault status hardcoded** as "Active" in Insights tab despite DashboardShell already fetching it
9. **Agent card has no link** while Vault and Memory cards do
10. **WebSocket authentication** — the hook fetches `wsUrl` from `/api/env` but does NOT pass auth token in the WS URL (line 82: `new WebSocket(${backendUrl}${path})`), while backend expects `?token=...` query param (ws_system.py line 61). The hook does not append the token.

### WebSocket Auth Bug Detail
- **Backend expects:** `ws://.../ws/system?token=xxx` (ws_system.py line 61: `token: str = Query(None)`)
- **Frontend sends:** `ws://.../ws/system` (useSystemWebSocket.ts line 82: no query param)
- This means the WebSocket will always receive `token=None` and close with code 4001
- The HTTP fallback (30s polling) works around this, so metrics still load but with delay

---

## 11. File Reference Index

| Purpose | Absolute Path | Lines |
|---------|---------------|-------|
| Dashboard page | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.tsx` | 318 |
| Dashboard loading | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/loading.tsx` | 10 |
| Dashboard error | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/error.tsx` | 28 |
| Dashboard test | `/home/adi/Desktop/Cortex-Workspace/frontend/app/app/page.test.tsx` | 145 |
| DashboardShell | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/layout/DashboardShell.tsx` | 601 |
| MetricRing | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/MetricRing.tsx` | 86 |
| TabGroup | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/TabGroup.tsx` | 98 |
| NeuralNetwork | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/NeuralNetwork.tsx` | 479 |
| Card | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/Card.tsx` | 49 |
| PageTransition | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/ui/PageTransition.tsx` | 23 |
| SyncStatus | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/components/SyncStatus.tsx` | 615 |
| useSystemWebSocket | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/hooks/useSystemWebSocket.ts` | 149 |
| cortexApi (system) | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/auth/cortexApi.ts` | 506-512 |
| memoryApi | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/api/memory.ts` | 59 |
| agentApi | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/api/agent.ts` | 118 |
| API index | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/api/index.ts` | 14 |
| Types | `/home/adi/Desktop/Cortex-Workspace/frontend/src/shared/types.ts` | 175-211 |
| Backend system.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/api/v1/system.py` | 70 |
| Backend ws_system.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/api/v1/ws_system.py` | 92 |
| Backend system_info.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/core/system_info.py` | 197 |
| Backend logging.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/core/logging.py` | 100 |
| Backend schemas/system.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/schemas/system.py` | 32 |
| Backend router.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/api/router.py` | 58 |
| Backend main.py | `/home/adi/Desktop/Cortex-Workspace/backend/app/main.py` | 213 (ws_router) |
