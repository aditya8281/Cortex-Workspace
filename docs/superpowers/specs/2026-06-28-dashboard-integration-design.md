Last updated: 2026-06-28

# Dashboard Real Integration Design Spec

## Overview

Replace hardcoded dashboard components with real backend API data. Currently only `RecentActivity` fetches real data; `SystemOverview`, `MetricsRow`, and `QuickActions` use static mock data.

## Backend Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/system/health/live` | GET | Liveness status |
| `/system/health/ready` | GET | Database connectivity |
| `/system/health/deep` | GET | Full health (DB, Redis, disk, memory) |
| `/system/metrics` | GET | CPU%, RAM, GPU, disk, top processes |
| `/models/health` | GET | LLM provider health, latency |
| `/models/metrics` | GET | Token usage, request count |
| `/conversations?limit=5` | GET | Recent conversations |

## Current Components

| Component | Current State | Target |
|-----------|--------------|--------|
| `SystemOverview` | Hardcoded CPU/RAM/Disk cards | Real `GET /system/metrics` data |
| `MetricsRow` | Hardcoded request/token/latency cards | Real `GET /models/metrics` + `GET /models/health` |
| `QuickActions` | Static action cards | Keep as-is (navigation shortcuts) |
| `RecentActivity` | Fetches from conversations API | Already real — no change |

## Changes

### 1. Update `dashboard/api.ts`

Fix types to match actual backend responses:

```typescript
// Current SystemMetrics type is wrong — backend returns different fields
// Backend returns: cpu_percent, ram_total_gb, ram_used_gb, ram_percent, gpu_name, gpu_type, gpu_percent, disk_total_gb, disk_used_gb, disk_percent, processes[]

export interface SystemMetrics {
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  gpu_name: string;
  gpu_type: string;
  gpu_percent: number | null;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  processes: ProcessInfo[];
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu: number;
  memory: number;
  status: string;
}

export interface LLMHealthResponse {
  status: string;
  latency_ms: number;
  error: string | null;
}

export interface LLMMetricsResponse {
  total_requests: number;
  total_tokens: number;
  avg_latency: number;
}
```

Update `dashboardApi` to use correct paths:
- `getMetrics()` → `GET /system/metrics`
- `getLLMHealth()` → `GET /models/health`
- `getLLMMetrics()` → `GET /models/metrics`
- `getDeepHealth()` → `GET /system/health/deep`

### 2. Update `SystemOverview` component

Replace hardcoded values with real data from `GET /system/metrics`:
- CPU usage bar (real `cpu_percent`)
- RAM usage bar (real `ram_used_gb` / `ram_total_gb`)
- GPU info (real `gpu_name`, `gpu_percent`)
- Disk usage (real `disk_used_gb` / `disk_total_gb`)
- Top processes list (real `processes[]`)
- Loading skeleton while fetching
- Auto-refresh every 10 seconds

### 3. Update `MetricsRow` component

Replace hardcoded values:
- Request count from `GET /models/metrics` → `total_requests`
- Token usage from `GET /models/metrics` → `total_tokens`
- LLM status from `GET /models/health` → `status` + `latency_ms`
- Loading skeleton while fetching

### 4. Keep `QuickActions` as-is

Navigation shortcuts (New Chat, Browse Models, View Agents, System Health) — these are links, not data.

### 5. Keep `RecentActivity` as-is

Already fetches real data from conversations API.

## Files

| Action | File |
|--------|------|
| Modify | `features/dashboard/api.ts` — fix types + add LLM metrics endpoint |
| Modify | `features/dashboard/components/SystemOverview.tsx` — real data |
| Modify | `features/dashboard/components/MetricsRow.tsx` — real data |
| **Total** | **2 modified** |

## Loading States

- Each card shows skeleton while its specific API call is in progress
- Graceful degradation: if metrics fail, show "Unavailable" instead of crashing
- Auto-refresh with visual indicator (last updated timestamp)

## Anti-Slop

- Progress bars use CSS with `transition-[width]`
- No identical card grids — each metric card has unique layout
- Color-coded bars: green <70%, yellow 70-85%, red >85%
