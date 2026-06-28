# Dashboard Real Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace hardcoded dashboard components with real backend API data.

**Architecture:** Fix types in dashboard/api.ts, then update SystemOverview and MetricsRow to fetch real data.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS.

## Global Constraints

- Dark-only. All colors from DESIGN.md tokens.
- No `transition-all`, `h-screen`, gradient text, glassmorphism.
- Motion: hover 150ms, ease-out-quart. `transition-[width]` for progress bars.
- Color-coded bars: green <70%, yellow 70-85%, red >85%.

## Existing Files

- `frontend/src/features/dashboard/api.ts` — types and API client (NEEDS FIX)
- `frontend/src/features/dashboard/components/SystemOverview.tsx` — hardcoded data
- `frontend/src/features/dashboard/components/MetricsRow.tsx` — hardcoded data

## Backend Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/system/health/live` | GET | Liveness status |
| `/system/health/ready` | GET | DB connectivity |
| `/system/health/deep` | GET | Full health (DB, Redis, disk, memory) |
| `/system/metrics` | GET | CPU%, RAM, GPU, disk, processes |
| `/models/health` | GET | LLM provider health, latency |
| `/models/metrics` | GET | Token usage, request count |

---

### Task 1: Fix api.ts Types

**Files:**
- Modify: `frontend/src/features/dashboard/api.ts`

- [ ] **Step 1: Replace api.ts with corrected types and endpoints**

```typescript
"use client";

import { apiFetch } from "@/shared/api/client";

// ── System Metrics ──────────────────────────────────────────────────────

export interface SystemMetrics {
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  gpu_name: string | null;
  gpu_type: string | null;
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

// ── LLM Health ──────────────────────────────────────────────────────────

export interface LLMHealthResponse {
  status: string;
  latency_ms: number;
  error: string | null;
}

// ── LLM Metrics ─────────────────────────────────────────────────────────

export interface LLMMetricsResponse {
  total_requests: number;
  total_tokens: number;
  avg_latency: number;
}

// ── Deep Health ─────────────────────────────────────────────────────────

export interface DeepHealth {
  status: string;
  database: { status: string; latency_ms: number };
  redis: { status: string; latency_ms: number } | null;
  disk: { status: string; percent: number };
  memory: { status: string; percent: number };
}

// ── API Client ──────────────────────────────────────────────────────────

export const dashboardApi = {
  getMetrics: () => apiFetch<SystemMetrics>("/system/metrics"),
  getLLMHealth: () => apiFetch<LLMHealthResponse>("/models/health"),
  getLLMMetrics: () => apiFetch<LLMMetricsResponse>("/models/metrics"),
  getDeepHealth: () => apiFetch<DeepHealth>("/system/health/deep"),
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/dashboard/api.ts
git commit -m "fix(dashboard): correct types and endpoints to match actual backend"
```

---

### Task 2: Update SystemOverview

**Files:**
- Modify: `frontend/src/features/dashboard/components/SystemOverview.tsx`

- [ ] **Step 1: Replace SystemOverview with real data fetching**

Read the current file first, then replace with this pattern:

```tsx
"use client";

import { useState, useEffect } from "react";
import { dashboardApi } from "../api";
import type { SystemMetrics } from "../api";
import { Card } from "@/shared/ui/Card";

export function SystemOverview() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = () => {
      dashboardApi.getMetrics().then(setMetrics).catch(() => {}).finally(() => setLoading(false));
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-bg-elevated animate-pulse" />
        ))}
      </div>
    );
  }

  if (!metrics) return null;

  const stats = [
    { label: "CPU", value: `${metrics.cpu_percent}%`, percent: metrics.cpu_percent },
    { label: "RAM", value: `${metrics.ram_used_gb} / ${metrics.ram_total_gb} GB`, percent: metrics.ram_percent },
    { label: "GPU", value: metrics.gpu_percent !== null ? `${metrics.gpu_percent}%` : "N/A", percent: metrics.gpu_percent ?? 0, name: metrics.gpu_name },
    { label: "Disk", value: `${metrics.disk_used_gb} / ${metrics.disk_total_gb} GB`, percent: metrics.disk_percent },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map((stat) => (
        <Card key={stat.label} className="p-3" role="article" aria-label={`${stat.label} usage`}>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-text-muted">{stat.label}</span>
            <span className="text-xs font-mono text-text-secondary">{stat.value}</span>
          </div>
          <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
            <div
              className={`h-full rounded-full transition-[width] duration-500 ease-out ${stat.percent >= 85 ? "bg-danger" : stat.percent >= 70 ? "bg-warning" : "bg-success"}`}
              style={{ width: `${Math.min(stat.percent, 100)}%` }}
              role="progressbar"
              aria-valuenow={stat.percent}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          {stat.name && <p className="text-[10px] text-text-muted mt-1 truncate">{stat.name}</p>}
        </Card>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Add top processes list below bars (optional enhancement)**

If the current SystemOverview shows processes, add this to the component above:

```tsx
{metrics.processes.length > 0 && (
  <Card className="p-3 mt-3">
    <h3 className="text-xs font-semibold text-text-primary mb-2">Top Processes</h3>
    <div className="space-y-1">
      {metrics.processes.slice(0, 5).map((proc) => (
        <div key={proc.pid} className="flex items-center justify-between text-xs">
          <span className="text-text-secondary font-mono truncate">{proc.name}</span>
          <div className="flex gap-3 text-text-muted">
            <span>CPU {proc.cpu}%</span>
            <span>RAM {proc.memory}%</span>
          </div>
        </div>
      ))}
    </div>
  </Card>
)}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/dashboard/components/SystemOverview.tsx
git commit -m "feat(dashboard): replace SystemOverview with real metrics data"
```

---

### Task 3: Update MetricsRow

**Files:**
- Modify: `frontend/src/features/dashboard/components/MetricsRow.tsx`

- [ ] **Step 1: Replace MetricsRow with real data fetching**

```tsx
"use client";

import { useState, useEffect } from "react";
import { dashboardApi } from "../api";
import type { LLMMetricsResponse, LLMHealthResponse } from "../api";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";

export function MetricsRow() {
  const [metrics, setMetrics] = useState<LLMMetricsResponse | null>(null);
  const [health, setHealth] = useState<LLMHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      dashboardApi.getLLMMetrics().catch(() => null),
      dashboardApi.getLLMHealth().catch(() => null),
    ]).then(([m, h]) => {
      setMetrics(m);
      setHealth(h);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-bg-elevated animate-pulse" />
        ))}
      </div>
    );
  }

  const statusColor = health?.status === "healthy" ? "success" : health?.status === "degraded" ? "warning" : "danger";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <Card className="p-3" role="article" aria-label="Request count">
        <span className="text-xs text-text-muted">Total Requests</span>
        <p className="text-lg font-semibold text-text-primary font-mono mt-0.5">{metrics?.total_requests?.toLocaleString() ?? "0"}</p>
      </Card>
      <Card className="p-3" role="article" aria-label="Token usage">
        <span className="text-xs text-text-muted">Tokens Used</span>
        <p className="text-lg font-semibold text-text-primary font-mono mt-0.5">{metrics?.total_tokens?.toLocaleString() ?? "0"}</p>
      </Card>
      <Card className="p-3" role="article" aria-label="LLM status">
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-muted">LLM Status</span>
          <div className="flex items-center gap-1.5">
            <StatusDot color={health ? statusColor as any : "warning"} />
            <span className="text-xs text-text-secondary capitalize">{health?.status ?? "Unknown"}</span>
          </div>
        </div>
        {health?.latency_ms !== undefined && (
          <p className="text-xs text-text-muted mt-1">Latency: {health.latency_ms}ms</p>
        )}
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/dashboard/components/MetricsRow.tsx
git commit -m "feat(dashboard): replace MetricsRow with real LLM metrics and health"
```

---

### Task 4: Final Build Validation

- [ ] **Step 1: Full build**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

- [ ] **Step 2: Verify no hardcoded values remain**

```bash
grep -n 'cpu.*85\|ram.*16\|disk.*500\|requests.*1234\|tokens.*500' frontend/src/features/dashboard/components/
```

- [ ] **Step 3: Verify progress bar color coding works**

```bash
grep -n 'bg-danger\|bg-warning\|bg-success' frontend/src/features/dashboard/components/SystemOverview.tsx
```

---

## Summary

| Task | What It Builds | Files |
|------|---------------|-------|
| 1 | Fix API types + endpoints | 1 modified |
| 2 | Real SystemOverview with metrics | 1 modified |
| 3 | Real MetricsRow with LLM health | 1 modified |
| 4 | Build validation | 0 |
| **Total** | | **3 modified** |
