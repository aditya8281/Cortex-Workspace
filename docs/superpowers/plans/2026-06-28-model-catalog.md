Last updated: 2026-06-28

# Model Catalog + Download Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full-featured `/models` page with Browse, Compare, Downloads, Installed tabs — plus Chat model selector and corrected API client paths.

**Architecture:** Single page at `/models` with four tabs. API clients re-export from existing `developer/api.ts` and `integration/api.ts` after fixing their URL paths. New components in `features/models/`. Chat gets model selector dropdown. Sidebar gets new nav link.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, Tailwind CSS (DESIGN.md tokens), existing shared UI (Card, Badge, Button, Input, Modal, EmptyState, Skeleton, StatusDot, Dropdown).

## Global Constraints

- Dark-only design. All colors from `tailwind.config.ts` tokens (void, bg-elevated, bg-surface, bg-hover, accent, text-primary/secondary/muted, border-subtle, danger, success, warning).
- Font: Geist (`font-sans`), JetBrains Mono (`font-mono`).
- No `transition-all` — use specific properties. No `h-screen` — use `dvh`. No gradient text, glassmorphism.
- Accessibility: WCAG AA 4.5:1 contrast, `prefers-reduced-motion`, focus-visible rings, 44px min touch targets.
- Motion budgets: hover 150ms, modal 250ms, ease-out-quart.
- All pages use `"use client"` directive.
- API calls via `apiFetch` from `@/shared/api/client`.
- No external charting libraries — CSS bars only for comparison.

## Critical Fix: Backend URL Paths

**BUG FOUND:** The existing `developer/api.ts` and `integration/api.ts` use wrong URL prefixes.

| Client | Current Path | Correct Path |
|--------|-------------|-------------|
| `developer/api.ts` catalog.list | `/developer/models` | `/models` |
| `developer/api.ts` catalog.recommended | `/developer/models/recommended` | `/models/recommended` |
| `developer/api.ts` catalog.hardware | `/developer/models/hardware` | `/models/hardware` |
| `developer/api.ts` catalog.search | `/developer/models/search` | `/models/search` |
| `developer/api.ts` catalog.compare | `/developer/models/compare` | `/models/compare` |
| `developer/api.ts` catalog.autocomplete | `/developer/models/autocomplete` | `/models/autocomplete` |
| `developer/api.ts` catalog.detail | `/developer/models/${id}` | `/models/${id}` |
| `developer/api.ts` catalog.inferenceConfig | `/developer/models/${id}/inference-config` | `/models/${id}/inference-config` |
| `developer/api.ts` github.list | `/developer/github` | `/me/github` |
| `developer/api.ts` github.add | `/developer/github` | `/me/github` |
| `developer/api.ts` github.remove | `/developer/github` | `/me/github` |
| `integration/api.ts` sync.defaults | `/integration/sync/defaults` | `/sync/defaults` |
| `integration/api.ts` sync.start | `/integration/sync/start` | `/sync/start` |
| `integration/api.ts` sync.validatePath | `/integration/sync/validate-path` | `/sync/validate-path` |
| `integration/api.ts` sync.stop | `/integration/sync/stop` | `/sync/stop` |
| `integration/api.ts` sync.status | `/integration/sync/status` | `/sync/status` |
| `integration/api.ts` sync.jobs | `/integration/sync/jobs` | `/sync/jobs` |
| `integration/api.ts` sync.job | `/integration/sync/jobs/${id}` | `/sync/jobs/${id}` |

Task 1 fixes these. All downstream tasks use correct paths.

---

## File Structure

```
frontend/src/
├── features/models/
│   ├── api.ts                        # Merged API client + types
│   ├── page.tsx                      # Client component with tabs + state
│   └── components/
│       ├── HardwareBar.tsx           # Hardware detection display
│       ├── BrowseView.tsx            # Browse tab: filters + card grid
│       ├── ModelCard.tsx             # Model card (Browse + Installed)
│       ├── CompareView.tsx           # Visual bar comparison
│       ├── DownloadsView.tsx         # Download queue/history
│       ├── InstalledView.tsx         # Installed models grid
│       ├── ModelDetailModal.tsx      # Full model detail modal
│       └── VariantPicker.tsx         # Variant selection dropdown
├── app/models/page.tsx              # Route page (re-export)
├── shared/layout/Sidebar.tsx        # Add Models nav link
├── features/chat/page.tsx           # Add model selector
├── features/developer/api.ts        # Fix URL paths
└── features/integration/api.ts      # Fix URL paths + add download endpoints
```

---

### Task 1: Fix Existing API Client URL Paths

**Files:**
- Modify: `frontend/src/features/developer/api.ts`
- Modify: `frontend/src/features/integration/api.ts`

**Interfaces:**
- Produces: Corrected API clients that all downstream tasks consume.

- [ ] **Step 1: Fix developer/api.ts catalog paths**

Replace every `/developer/models` with `/models` and `/developer/github` with `/me/github`:

```typescript
// frontend/src/features/developer/api.ts

/**
 * Developer API Client — Code Intelligence & GitHub
 *
 * Backend routes: /api/v1/models/*, /api/v1/me/github
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  description: string;
  html_url: string;
  language: string;
  stargazers_count: number;
  updated_at: string;
}

export interface ModelCatalogEntry {
  name: string;
  display_name: string;
  provider: string;
  model_type: string;
  parameter_count: number | null;
  size_bytes: number | null;
  context_length: number | null;
  capabilities: string[];
  description: string;
  downloaded: boolean;
  variants: ModelVariantEntry[];
  hardware_requirements: { min_ram_gb: number; recommended_ram_gb: number } | null;
}

export interface ModelVariantEntry {
  variant_id: string;
  quantization: string;
  size_bytes: number | null;
  size_gb: number | null;
  downloaded: boolean;
  quality_score: number | null;
}

export interface HardwareInfo {
  ram_gb: number;
  ram_available_gb: number;
  ram_percent: number;
  cpu_count: number;
  cpu_threads: number;
  cpu_freq_mhz: number;
  cpu_arch: string;
  gpu: Record<string, any>;
  disk_free_gb: number;
  supports_cuda: boolean;
  supports_metal: boolean;
}

export interface ModelComparison {
  winner_model: string;
  dimension_wins: Record<string, string>;
  dimensions: {
    dimension: string;
    display_name: string;
    values: Record<string, any>;
    winner: string;
    higher_is_better: boolean;
  }[];
  summary: string;
}

export interface RecommendedModel {
  model_id: string;
  display_name: string;
  family: string;
  parameter_count: number;
  capabilities: string[];
  description: string;
  score: number;
  explanation: { why: string; tradeoff: string; suitability: string };
}

// ── GitHub ─────────────────────────────────────────────────────────────────

export const github = {
  list: () =>
    apiFetch<{ items: GitHubRepo[] }>("/me/github"),

  add: (data: { repo_url: string }) =>
    apiFetch<GitHubRepo>("/me/github", { method: "POST", body: data }),

  remove: (data: { repo_id: number }) =>
    apiFetch<{ removed: boolean }>("/me/github", { method: "DELETE", body: data }),
};

// ── Model Catalog ──────────────────────────────────────────────────────────

export const catalog = {
  list: (params?: { model_type?: string; downloaded_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.model_type) searchParams.set("model_type", params.model_type);
    if (params?.downloaded_only) searchParams.set("downloaded_only", "true");
    const qs = searchParams.toString();
    return apiFetch<{
      models: ModelCatalogEntry[];
      total_count: number;
      downloaded_count: number;
      available_from_providers: { provider: string; model_count: number }[];
      type_counts: Record<string, number>;
      size_counts: Record<string, number>;
      catalog_status: Record<string, string>;
    }>(`/models${qs ? `?${qs}` : ""}`);
  },

  recommended: (workload?: string) => {
    const qs = workload ? `?workload=${encodeURIComponent(workload)}` : "";
    return apiFetch<{
      hardware: Record<string, any>;
      workloads: Record<string, { recommendations: RecommendedModel[] }>;
    }>(`/models/recommended${qs}`);
  },

  hardware: () =>
    apiFetch<HardwareInfo>("/models/hardware"),

  search: (params: { q?: string; capabilities?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params.q) searchParams.set("q", params.q);
    if (params.capabilities) searchParams.set("capabilities", params.capabilities);
    if (params.limit) searchParams.set("limit", String(params.limit));
    return apiFetch<{ models: ModelCatalogEntry[]; total_count: number }>(
      `/models/search?${searchParams.toString()}`
    );
  },

  compare: (model_ids: string[]) =>
    apiFetch<ModelComparison>("/models/compare", {
      method: "POST",
      body: { model_ids },
    }),

  autocomplete: (q: string) =>
    apiFetch<{ suggestions: string[] }>(
      `/models/autocomplete?q=${encodeURIComponent(q)}`
    ),

  detail: (modelId: string) =>
    apiFetch<ModelCatalogEntry & { architecture?: string; license?: string; tags: string[]; benchmarks?: Record<string, any> }>(
      `/models/${modelId}`
    ),

  inferenceConfig: (modelId: string) =>
    apiFetch<{ model_id: string; context_length?: number; temperature: number; top_p: number; top_k: number; repeat_penalty: number; seed: number; num_predict: number; num_ctx?: number; image_resolution?: number }>(
      `/models/${modelId}/inference-config`
    ),
};
```

- [ ] **Step 2: Fix integration/api.ts paths + add download endpoints**

```typescript
// frontend/src/features/integration/api.ts

/**
 * Integration API Client — Downloads & Sync
 *
 * Backend routes: /api/v1/models/*, /api/v1/sync/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface SyncDefaults {
  directories: string[];
  ignore_patterns: string[];
  sync_interval: number;
}

export interface SyncJob {
  id: string;
  name: string;
  source_path: string;
  target_path: string;
  status: "idle" | "syncing" | "paused" | "error";
  last_sync: string;
  file_count: number;
  error_message: string | null;
}

export interface SyncStatus {
  active: boolean;
  jobs: number;
  last_sync: string;
}

export interface InstalledModel {
  model_id: string;
  display_name: string;
  family: string;
  parameter_count: number | null;
  capabilities: string[];
  variants: {
    variant_id: string;
    quantization: string;
    size_bytes: number;
    size_gb: number;
    downloaded: boolean;
    parameter_count: number | null;
    quality_score: number;
  }[];
}

export interface DownloadJob {
  job_id: string;
  model_id: string;
  status: string;
  progress: number;
  speed_bytes_sec: number | null;
  downloaded_bytes: number;
  total_bytes: number;
  eta_seconds: number | null;
  queue_position: number | null;
  error: string | null;
}

export interface DownloadHistoryItem {
  job_id: string;
  model_id: string;
  status: string;
  progress: number;
  downloaded_bytes: number;
  total_bytes: number;
  error: string | null;
  completed_at: string | null;
  created_at: string;
}

// ── Sync ───────────────────────────────────────────────────────────────────

export const sync = {
  defaults: () =>
    apiFetch<SyncDefaults>("/sync/defaults"),

  start: (data: { source_path: string; target_path: string; name?: string }) =>
    apiFetch<SyncJob>("/sync/start", { method: "POST", body: data }),

  validatePath: (data: { path: string }) =>
    apiFetch<{ valid: boolean; writable: boolean; exists: boolean }>("/sync/validate-path", { method: "POST", body: data }),

  stop: (data: { job_id: string }) =>
    apiFetch<{ stopped: boolean }>("/sync/stop", { method: "POST", body: data }),

  status: () =>
    apiFetch<SyncStatus>("/sync/status"),

  jobs: () =>
    apiFetch<{ items: SyncJob[] }>("/sync/jobs"),

  job: (jobId: string) =>
    apiFetch<SyncJob>(`/sync/jobs/${jobId}`),
};

// ── Downloads ──────────────────────────────────────────────────────────────

export const downloads = {
  installed: () =>
    apiFetch<{ models: InstalledModel[]; installed_count: number }>("/models/installed"),

  syncInstalled: () =>
    apiFetch<{ matched: number; created: number; deleted: number; errors: string[] }>("/models/installed/sync", { method: "POST" }),

  queue: () =>
    apiFetch<{ active: DownloadJob[]; queued: DownloadJob[]; completed: DownloadJob[]; failed: DownloadJob[] }>("/models/downloads/queue"),

  history: (limit = 20) =>
    apiFetch<{ history: DownloadHistoryItem[] }>(`/models/downloads/history?limit=${limit}`),

  download: (modelName: string, variant?: string) =>
    apiFetch<{ status: string; model: string; variant?: string; download_id?: string }>(
      `/models/${modelName}/download${variant ? `?variant=${encodeURIComponent(variant)}` : ""}`,
      { method: "POST" }
    ),

  progress: (modelName: string) =>
    apiFetch<{ model: string; progress: number }>(`/models/${modelName}/progress`),

  cancel: (modelName: string) =>
    apiFetch<{ cancelled: boolean }>(`/models/${modelName}/cancel`, { method: "POST" }),

  remove: (modelName: string) =>
    apiFetch<{ status: string; model: string }>(`/models/${modelName}`, { method: "DELETE" }),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/developer/api.ts frontend/src/features/integration/api.ts
git commit -m "fix: correct API client URL paths for models and sync endpoints"
```

---

### Task 2: Create models/api.ts — Merged API Client + Types

**Files:**
- Create: `frontend/src/features/models/api.ts`

**Interfaces:**
- Consumes: `catalog` from `developer/api.ts`, `downloads` from `integration/api.ts`
- Produces: Re-exports + `ModelWithFit`, `HardwareInfoResponse` types for all downstream components.

- [ ] **Step 1: Create the merged API client**

```typescript
// frontend/src/features/models/api.ts

/**
 * Models API Client — merges catalog + downloads + adds page-specific types
 *
 * Backend routes: /api/v1/models/* (catalog + downloads)
 */
export { catalog } from "@/features/developer/api";
export { downloads, sync } from "@/features/integration/api";
export type {
  ModelCatalogEntry,
  ModelVariantEntry,
  HardwareInfo,
  ModelComparison,
  RecommendedModel,
  InstalledModel,
  DownloadJob,
  DownloadHistoryItem,
} from "@/features/developer/api";
export type {
  InstalledModel as InstalledModelDownload,
} from "@/features/integration/api";

// ── Page-specific types ────────────────────────────────────────────────────

export type RamFitStatus = "good" | "tight" | "insufficient";

export interface ModelWithFit {
  model_id: string;
  display_name: string;
  provider: string;
  parameter_count: number | null;
  size_bytes: number | null;
  context_length: number | null;
  capabilities: string[];
  description: string;
  downloaded: boolean;
  variants: {
    variant_id: string;
    quantization: string;
    size_bytes: number | null;
    size_gb: number | null;
    downloaded: boolean;
    quality_score: number | null;
  }[];
  hardware_requirements: { min_ram_gb: number; recommended_ram_gb: number } | null;
  ramFitPercent: number;
  ramFitStatus: RamFitStatus;
  isDefault: boolean;
}

export type TabKey = "browse" | "compare" | "downloads" | "installed";

export interface DownloadProgress {
  model: string;
  progress: number;
  speed_bytes_sec: number | null;
  eta_seconds: number | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const STORAGE_KEY = "cortex_default_model";

export function getDefaultModel(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setDefaultModel(modelId: string): void {
  localStorage.setItem(STORAGE_KEY, modelId);
}

export function calculateRamFit(
  ramGb: number,
  minRamNeeded: number | null,
): { percent: number; status: RamFitStatus } {
  if (!minRamNeeded || minRamNeeded <= 0) return { percent: 100, status: "good" };
  const percent = Math.min(100, Math.round((ramGb / minRamNeeded) * 100));
  const status: RamFitStatus = percent >= 100 ? "good" : percent >= 50 ? "tight" : "insufficient";
  return { percent, status };
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export function formatSpeed(bytesPerSec: number): string {
  if (bytesPerSec <= 0) return "—";
  return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
}

export function formatEta(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s remaining`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s remaining`;
}

export function formatParamCount(count: number | null): string {
  if (count === null) return "Unknown";
  if (count >= 1_000_000_000) return `${(count / 1_000_000_000).toFixed(1)}B`;
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(0)}M`;
  return `${count}`;
}
```

- [ ] **Step 2: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30`
Expected: No errors from this file (may have pre-existing errors from other files).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/api.ts
git commit -m "feat(models): add merged API client with types and helpers"
```

---

### Task 3: Create HardwareBar Component

**Files:**
- Create: `frontend/src/features/models/components/HardwareBar.tsx`

**Interfaces:**
- Consumes: `HardwareInfo` from `models/api.ts`, `catalog.hardware()`
- Produces: `<HardwareBar />` component accepting `hardware: HardwareInfo | null`.

- [ ] **Step 1: Create HardwareBar component**

```tsx
// frontend/src/features/models/components/HardwareBar.tsx

"use client";

import type { HardwareInfo } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";

interface HardwareBarProps {
  hardware: HardwareInfo | null;
  loading?: boolean;
}

function RamBar({ used, total }: { used: number; total: number }) {
  const percent = total > 0 ? Math.round(((total - used) / total) * 100) : 0;
  const color =
    percent >= 70 ? "bg-success" : percent >= 40 ? "bg-warning" : "bg-danger";

  return (
    <div className="flex items-center gap-2 min-w-0">
      <span className="text-xs text-text-muted whitespace-nowrap">
        {total}GB
      </span>
      <div className="flex-1 h-1.5 rounded-full bg-bg-surface overflow-hidden">
        <div
          className={`h-full rounded-full transition-[width] duration-300 ${color}`}
          style={{ width: `${Math.max(0, 100 - percent)}%` }}
          role="progressbar"
          aria-valuenow={100 - percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${100 - percent}% RAM used`}
        />
      </div>
      <span className="text-xs text-text-secondary whitespace-nowrap">
        {total - used}GB free
      </span>
    </div>
  );
}

function SkeletonBar() {
  return (
    <div className="flex items-center gap-4 animate-pulse">
      <div className="h-4 w-20 rounded bg-bg-surface" />
      <div className="flex-1 h-1.5 rounded-full bg-bg-surface" />
      <div className="h-4 w-16 rounded bg-bg-surface" />
    </div>
  );
}

export function HardwareBar({ hardware, loading }: HardwareBarProps) {
  if (loading) {
    return (
      <Card className="px-4 py-3">
        <SkeletonBar />
      </Card>
    );
  }

  if (!hardware) {
    return (
      <Card className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">
            Hardware detection unavailable — start Ollama to enable hardware info
          </span>
        </div>
      </Card>
    );
  }

  const gpuName = hardware.gpu?.name || hardware.gpu?.model || null;
  const vram = hardware.gpu?.vram_total_gb || hardware.gpu?.memory_total_gb || null;

  return (
    <Card className="px-4 py-3">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs">
        {/* RAM */}
        <div className="flex items-center gap-2 min-w-[180px]">
          <span className="text-text-muted font-mono w-7">RAM</span>
          <RamBar used={hardware.ram_gb - hardware.ram_available_gb} total={hardware.ram_gb} />
        </div>

        {/* GPU */}
        <div className="flex items-center gap-2">
          <span className="text-text-muted font-mono w-7">GPU</span>
          {gpuName ? (
            <span className="text-text-secondary">
              {gpuName}
              {vram ? ` · ${vram}GB` : ""}
            </span>
          ) : (
            <span className="text-text-muted">No GPU</span>
          )}
        </div>

        {/* CUDA/Metal badges */}
        {hardware.supports_cuda && <Badge variant="success">CUDA</Badge>}
        {hardware.supports_metal && <Badge variant="success">Metal</Badge>}

        {/* CPU */}
        <div className="flex items-center gap-2">
          <span className="text-text-muted font-mono w-7">CPU</span>
          <span className="text-text-secondary">
            {hardware.cpu_threads || hardware.cpu_count} cores · {hardware.cpu_arch}
          </span>
        </div>

        {/* Disk */}
        <div className="flex items-center gap-2">
          <span className="text-text-muted font-mono w-7">Disk</span>
          <span className="text-text-secondary">{hardware.disk_free_gb}GB free</span>
        </div>
      </div>
    </Card>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/models/components/HardwareBar.tsx
git commit -m "feat(models): add HardwareBar component"
```

---

### Task 4: Create ModelCard Component

**Files:**
- Create: `frontend/src/features/models/components/ModelCard.tsx`

**Interfaces:**
- Consumes: `ModelWithFit` from `models/api.ts`, `formatBytes`, `formatParamCount`, `calculateRamFit` helpers
- Produces: `<ModelCard />` — renders a model with download/view/compare actions

- [ ] **Step 1: Create ModelCard component**

```tsx
// frontend/src/features/models/components/ModelCard.tsx

"use client";

import type { ModelWithFit, RamFitStatus } from "../api";
import { formatBytes, formatParamCount } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";

interface ModelCardProps {
  model: ModelWithFit;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelected: boolean;
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
  downloading?: boolean;
  downloadProgress?: number;
  onCancelDownload?: (modelId: string) => void;
}

const fitColors: Record<RamFitStatus, string> = {
  good: "bg-success",
  tight: "bg-warning",
  insufficient: "bg-danger",
};

const fitLabels: Record<RamFitStatus, string> = {
  good: "Good fit",
  tight: "Tight",
  insufficient: "Low RAM",
};

export function ModelCard({
  model,
  onDownload,
  onViewDetail,
  compareSelected,
  onToggleCompare,
  compareDisabled,
  downloading,
  downloadProgress,
  onCancelDownload,
}: ModelCardProps) {
  const primaryVariant = model.variants?.[0];
  const minRam = model.hardware_requirements?.min_ram_gb ?? null;

  return (
    <Card className="p-4 flex flex-col gap-3" role="article" aria-label={model.display_name}>
      {/* Header: name + badges */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-title font-semibold text-text-primary leading-tight">
          {model.display_name}
        </h3>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {model.downloaded && (
            <Badge variant="success">Installed</Badge>
          )}
        </div>
      </div>

      {/* Params + capabilities */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-text-secondary font-mono">
          {formatParamCount(model.parameter_count)} params
        </span>
        {model.capabilities?.map((cap) => (
          <Badge key={cap} variant="default">
            {cap}
          </Badge>
        ))}
      </div>

      {/* Size + variant */}
      {primaryVariant && (
        <p className="text-xs text-text-muted">
          {formatBytes(primaryVariant.size_bytes ?? 0)} · {primaryVariant.quantization}
        </p>
      )}

      {/* RAM fit */}
      {minRam && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">
            RAM: {minRam}GB needed
          </span>
        </div>
      )}

      {minRam && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-bg-surface overflow-hidden">
            <div
              className={`h-full rounded-full ${fitColors[model.ramFitStatus]}`}
              style={{ width: `${model.ramFitPercent}%` }}
              role="progressbar"
              aria-valuenow={model.ramFitPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${model.ramFitPercent}% RAM fit`}
            />
          </div>
          <span className="text-[0.625rem] text-text-muted font-mono w-12 text-right">
            {model.ramFitPercent}%
          </span>
        </div>
      )}

      {/* Downloading state */}
      {downloading && downloadProgress !== undefined && (
        <div className="space-y-1.5">
          <div className="h-2 rounded-full bg-bg-surface overflow-hidden">
            <div
              className="h-full rounded-full bg-accent transition-[width] duration-300"
              style={{ width: `${Math.round(downloadProgress * 100)}%` }}
              role="progressbar"
              aria-valuenow={Math.round(downloadProgress * 100)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Downloading ${model.display_name}: ${Math.round(downloadProgress * 100)}%`}
            />
          </div>
          <span className="text-xs text-text-muted">
            {Math.round(downloadProgress * 100)}%
          </span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-auto pt-1">
        {downloading ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onCancelDownload?.(model.model_id)}
            aria-label={`Cancel download of ${model.display_name}`}
          >
            Cancel
          </Button>
        ) : model.downloaded ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onViewDetail(model.model_id)}
          >
            View Details
          </Button>
        ) : (
          <Button
            size="sm"
            onClick={() => onDownload(model.model_id)}
            aria-label={`Download ${model.display_name}`}
          >
            Download
          </Button>
        )}

        <label className="flex items-center gap-1.5 ml-auto cursor-pointer">
          <input
            type="checkbox"
            checked={compareSelected}
            onChange={() => onToggleCompare(model.model_id)}
            disabled={!compareSelected && compareDisabled}
            className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface text-accent accent-accent"
            aria-label={`Add ${model.display_name} to comparison`}
          />
          <span className="text-xs text-text-muted">Compare</span>
        </label>
      </div>
    </Card>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/models/components/ModelCard.tsx
git commit -m "feat(models): add ModelCard component"
```

---

### Task 5: Create BrowseView Component

**Files:**
- Create: `frontend/src/features/models/components/BrowseView.tsx`

**Interfaces:**
- Consumes: `ModelWithFit`, `RecommendedModel`, `HardwareInfo` from `models/api.ts`, `catalog.*`, `ModelCard`
- Produces: `<BrowseView />` — full browse tab with filters, recommended section, card grid

- [ ] **Step 1: Create BrowseView component**

```tsx
// frontend/src/features/models/components/BrowseView.tsx

"use client";

import { useState, useEffect, useCallback } from "react";
import type { ModelWithFit, RecommendedModel, HardwareInfo, RamFitStatus } from "../api";
import { catalog, calculateRamFit, getDefaultModel } from "../api";
import { formatParamCount } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { ModelCard } from "./ModelCard";

interface BrowseViewProps {
  hardware: HardwareInfo | null;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelectedIds: string[];
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
  downloadingModels: Map<string, number>;
  onCancelDownload: (modelId: string) => void;
}

type SizeFilter = "small" | "medium" | "large" | null;

export function BrowseView({
  hardware,
  onDownload,
  onViewDetail,
  compareSelectedIds,
  onToggleCompare,
  compareDisabled,
  downloadingModels,
  onCancelDownload,
}: BrowseViewProps) {
  const [models, setModels] = useState<ModelWithFit[]>([]);
  const [recommended, setRecommended] = useState<RecommendedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [capabilityFilter, setCapabilityFilter] = useState<string[]>([]);
  const [sizeFilter, setSizeFilter] = useState<SizeFilter>(null);
  const [sort, setSort] = useState<string>("relevance");
  const [totalCount, setTotalCount] = useState(0);
  const defaultModel = getDefaultModel();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let result;
      if (debouncedQuery) {
        const caps = capabilityFilter.length > 0 ? capabilityFilter.join(",") : undefined;
        result = await catalog.search({ q: debouncedQuery, capabilities: caps, limit: 200 });
        result = { ...result, models: result.models.map(m => enrichModel(m)) };
      } else {
        const res = await catalog.list({ downloaded_only: false });
        let enriched = res.models.map(m => enrichModel(m));

        // Client-side capability filter
        if (capabilityFilter.length > 0) {
          enriched = enriched.filter(m =>
            capabilityFilter.some(c => m.capabilities.includes(c))
          );
        }

        result = { models: enriched, total_count: res.total_count };
      }

      // Client-side size filter
      let filtered = result.models;
      if (sizeFilter) {
        filtered = filtered.filter(m => {
          const params = m.parameter_count ?? 0;
          if (sizeFilter === "small") return params < 4_000_000_000;
          if (sizeFilter === "medium") return params >= 4_000_000_000 && params <= 14_000_000_000;
          return params > 14_000_000_000;
        });
      }

      // Sort
      if (sort !== "relevance") {
        filtered.sort((a, b) => {
          if (sort === "size_asc") return (a.size_bytes ?? 0) - (b.size_bytes ?? 0);
          if (sort === "size_desc") return (b.size_bytes ?? 0) - (a.size_bytes ?? 0);
          if (sort === "params_asc") return (a.parameter_count ?? 0) - (b.parameter_count ?? 0);
          if (sort === "params_desc") return (b.parameter_count ?? 0) - (a.parameter_count ?? 0);
          return 0;
        });
      }

      setModels(filtered);
      setTotalCount(result.total_count);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, capabilityFilter, sizeFilter, sort, hardware]);

  const enrichModel = (m: any): ModelWithFit => {
    const ram = hardware?.ram_gb ?? 32;
    const minRam = m.hardware_requirements?.min_ram_gb ?? null;
    const { percent, status } = calculateRamFit(ram, minRam);
    return {
      ...m,
      ramFitPercent: percent,
      ramFitStatus: status,
      isDefault: m.name === defaultModel,
    };
  };

  useEffect(() => { loadModels(); }, [loadModels]);

  // Load recommended on mount
  useEffect(() => {
    catalog.recommended().then(res => {
      const all = Object.values(res.workloads).flatMap(w => w.recommendations ?? []);
      setRecommended(all.slice(0, 4));
    }).catch(() => {});
  }, []);

  const toggleCapability = (cap: string) => {
    setCapabilityFilter(prev =>
      prev.includes(cap) ? prev.filter(c => c !== cap) : [...prev, cap]
    );
  };

  const capabilities = ["chat", "code", "vision"];

  return (
    <div className="space-y-6">
      {/* Recommended */}
      {recommended.length > 0 && !debouncedQuery && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Recommended for your hardware
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {recommended.map(rec => (
              <Card key={rec.model_id} className="p-3">
                <p className="text-sm font-medium text-text-primary mb-1">
                  {rec.display_name}
                </p>
                <p className="text-xs text-text-muted mb-2 line-clamp-2">
                  {rec.explanation?.why ?? rec.description}
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="default">{formatParamCount(rec.parameter_count)}</Badge>
                  <span className="text-[0.625rem] text-text-muted">
                    score: {Math.round(rec.score * 100)}%
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <Input
            label="Search models"
            placeholder="Search by name, capability..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Capability chips */}
        <div className="flex items-center gap-1.5">
          {capabilities.map(cap => (
            <button
              key={cap}
              onClick={() => toggleCapability(cap)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-150 ${
                capabilityFilter.includes(cap)
                  ? "bg-accent/12 text-accent"
                  : "bg-bg-surface text-text-muted hover:text-text-secondary"
              }`}
            >
              {cap}
            </button>
          ))}
        </div>

        {/* Size filter */}
        <div className="flex items-center gap-1.5">
          {(["small", "medium", "large"] as const).map(size => (
            <button
              key={size}
              onClick={() => setSizeFilter(sizeFilter === size ? null : size)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-150 ${
                sizeFilter === size
                  ? "bg-accent/12 text-accent"
                  : "bg-bg-surface text-text-muted hover:text-text-secondary"
              }`}
            >
              {size === "small" ? "<4B" : size === "medium" ? "4-14B" : ">14B"}
            </button>
          ))}
        </div>

        {/* Sort */}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="h-9 rounded-md border border-border-default bg-bg-surface px-2.5 text-xs text-text-secondary focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none"
          aria-label="Sort models"
        >
          <option value="relevance">Relevance</option>
          <option value="size_asc">Size ↑</option>
          <option value="size_desc">Size ↓</option>
          <option value="params_asc">Params ↑</option>
          <option value="params_desc">Params ↓</option>
        </select>
      </div>

      {/* Results count */}
      <p className="text-xs text-text-muted">
        {totalCount > 0 ? `${totalCount} models` : ""}
      </p>

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
          {error}
          <Button size="sm" variant="ghost" className="ml-2" onClick={loadModels}>
            Retry
          </Button>
        </div>
      )}

      {/* Card grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4 animate-pulse">
              <div className="space-y-3">
                <div className="h-5 w-3/4 rounded bg-bg-surface" />
                <div className="h-4 w-1/2 rounded bg-bg-surface" />
                <div className="h-3 w-1/3 rounded bg-bg-surface" />
                <div className="h-1.5 w-full rounded-full bg-bg-surface" />
              </div>
            </Card>
          ))}
        </div>
      ) : models.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {models.map(model => (
            <ModelCard
              key={model.name}
              model={model}
              onDownload={onDownload}
              onViewDetail={onViewDetail}
              compareSelected={compareSelectedIds.includes(model.name)}
              onToggleCompare={onToggleCompare}
              compareDisabled={compareDisabled}
              downloading={downloadingModels.has(model.name)}
              downloadProgress={downloadingModels.get(model.name)}
              onCancelDownload={onCancelDownload}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No models found"
          description={searchQuery ? "Try a different search query or filters" : "No models available in catalog"}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/models/components/BrowseView.tsx
git commit -m "feat(models): add BrowseView with filters and card grid"
```

---

### Task 6: Create CompareView Component

**Files:**
- Create: `frontend/src/features/models/components/CompareView.tsx`

**Interfaces:**
- Consumes: `catalog.compare()`, `ModelComparison` type
- Produces: `<CompareView />` — visual bar comparison for selected models

- [ ] **Step 1: Create CompareView component**

```tsx
// frontend/src/features/models/components/CompareView.tsx

"use client";

import { useState, useEffect } from "react";
import type { ModelComparison } from "../api";
import { catalog } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";

interface CompareViewProps {
  selectedIds: string[];
  onClearSelection: () => void;
  onDownloadModel: (modelId: string) => void;
}

export function CompareView({
  selectedIds,
  onClearSelection,
  onDownloadModel,
}: CompareViewProps) {
  const [comparison, setComparison] = useState<ModelComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedIds.length < 2) {
      setComparison(null);
      return;
    }

    setLoading(true);
    setError(null);
    catalog
      .compare(selectedIds)
      .then(setComparison)
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedIds]);

  if (selectedIds.length < 2) {
    return (
      <EmptyState
        title="Select models to compare"
        description="Check the compare checkbox on 2-5 model cards in the Browse tab"
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }

  if (!comparison) return null;

  // Find display names from dimension values
  const modelNames: Record<string, string> = {};
  if (comparison.dimensions.length > 0) {
    const firstDim = comparison.dimensions[0];
    for (const modelId of Object.keys(firstDim.values)) {
      // Extract name from model_id (e.g., "llama3.1:8b-q4_km" → "Llama3.1 8b")
      modelNames[modelId] = modelId.split(":")[0].replace(/[-_]/g, " ");
    }
  }

  return (
    <div className="space-y-6">
      {/* Model headers */}
      <div className="flex items-center gap-4 flex-wrap">
        {selectedIds.map(id => (
          <span
            key={id}
            className="text-sm font-medium text-text-primary"
          >
            {modelNames[id] ?? id}
          </span>
        ))}
      </div>

      {/* Dimensions */}
      {comparison.dimensions.map(dim => {
        const maxVal = Math.max(
          ...Object.values(dim.values).map(v => (typeof v === "number" ? v : 0))
        );

        return (
          <div key={dim.dimension} className="space-y-2">
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              {dim.display_name}
            </h4>
            <div className="space-y-1.5">
              {selectedIds.map(id => {
                const val = dim.values[id];
                const numVal = typeof val === "number" ? val : 0;
                const width = maxVal > 0 ? (numVal / maxVal) * 100 : 0;
                const isWinner = dim.winner === id;

                return (
                  <div key={id} className="flex items-center gap-3">
                    <span className="text-xs text-text-secondary w-24 truncate">
                      {modelNames[id] ?? id}
                    </span>
                    <div className="flex-1 h-3 rounded-sm bg-bg-surface overflow-hidden">
                      <div
                        className={`h-full rounded-sm transition-[width] duration-300 ${
                          isWinner ? "bg-accent" : "bg-bg-elevated"
                        }`}
                        style={{ width: `${Math.max(4, width)}%` }}
                      />
                    </div>
                    <span className="text-xs text-text-secondary font-mono w-16 text-right">
                      {typeof val === "number" ? val : String(val)}
                      {isWinner && (
                        <span className="ml-1 text-accent">★</span>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {/* Winner + actions */}
      {comparison.winner_model && (
        <Card className="p-4">
          <p className="text-sm text-text-secondary mb-1">
            Winner:{" "}
            <span className="font-semibold text-text-primary">
              {modelNames[comparison.winner_model] ?? comparison.winner_model}
            </span>
          </p>
          <p className="text-xs text-text-muted mb-3">{comparison.summary}</p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => onDownloadModel(comparison!.winner_model)}
            >
              Download Winner
            </Button>
            <Button size="sm" variant="ghost" onClick={onClearSelection}>
              Clear Selection
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/models/components/CompareView.tsx
git commit -m "feat(models): add CompareView with visual bar comparison"
```

---

### Task 7: Create DownloadsView Component

**Files:**
- Create: `frontend/src/features/models/components/DownloadsView.tsx`

**Interfaces:**
- Consumes: `downloads.queue()`, `downloads.history()`, `downloads.cancel()`, `downloads.download()`
- Produces: `<DownloadsView />` — download queue with active/queued/completed/failed sections

- [ ] **Step 1: Create DownloadsView component**

```tsx
// frontend/src/features/models/components/DownloadsView.tsx

"use client";

import { useState, useEffect, useRef } from "react";
import type { DownloadJob, DownloadHistoryItem } from "../api";
import { downloads } from "../api";
import { formatBytes, formatSpeed, formatEta } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DownloadsView() {
  const [active, setActive] = useState<DownloadJob[]>([]);
  const [queued, setQueued] = useState<DownloadJob[]>([]);
  const [completed, setCompleted] = useState<DownloadJob[]>([]);
  const [failed, setFailed] = useState<DownloadJob[]>([]);
  const [history, setHistory] = useState<DownloadHistoryItem[]>([]);
  const [showCompleted, setShowCompleted] = useState(false);
  const [showFailed, setShowFailed] = useState(true);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadQueue = async () => {
    try {
      const res = await downloads.queue();
      setActive(res.active);
      setQueued(res.queued);
      setCompleted(res.completed);
      setFailed(res.failed);
    } catch {
      // ignore
    }
  };

  const loadHistory = async () => {
    try {
      const res = await downloads.history(20);
      setHistory(res.history);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadQueue();
    loadHistory();
  }, []);

  // Poll while active downloads exist
  useEffect(() => {
    if (active.length > 0) {
      pollingRef.current = setInterval(() => {
        loadQueue();
      }, 2000);
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [active.length]);

  const handleCancel = async (modelName: string) => {
    try {
      await downloads.cancel(modelName);
      // Optimistic: move to failed
      setActive(prev => prev.filter(j => j.model_id !== modelName));
      setQueued(prev => prev.filter(j => j.model_id !== modelName));
      setFailed(prev => [
        ...prev,
        { job_id: `cancel-${Date.now()}`, model_id: modelName, status: "cancelled", progress: 0, speed_bytes_sec: null, downloaded_bytes: 0, total_bytes: 0, eta_seconds: null, queue_position: null, error: "Cancelled by user" },
      ]);
    } catch {
      // ignore
    }
  };

  const handleRetry = async (modelName: string) => {
    try {
      await downloads.download(modelName);
      setFailed(prev => prev.filter(j => j.model_id !== modelName));
      loadQueue();
    } catch {
      // ignore
    }
  };

  const totalItems = active.length + queued.length + completed.length + failed.length + history.length;

  if (totalItems === 0) {
    return (
      <EmptyState
        title="No downloads yet"
        description="Browse models to find one to download"
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Active downloads */}
      {active.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Active ({active.length})
          </h3>
          <div className="space-y-2">
            {active.map(job => {
              const percent = Math.round(job.progress * 100);
              return (
                <Card key={job.job_id} className="p-3">
                  <div className="flex items-center gap-3 mb-2">
                    <StatusDot color="accent" pulse />
                    <span className="text-sm text-text-primary font-mono flex-1 truncate">
                      {job.model_id}
                    </span>
                    <span className="text-xs text-text-muted font-mono">{percent}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-bg-surface overflow-hidden mb-2">
                    <div
                      className="h-full rounded-full bg-accent transition-[width] duration-300"
                      style={{ width: `${percent}%` }}
                      role="progressbar"
                      aria-valuenow={percent}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`Downloading ${job.model_id}: ${percent}%`}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">
                      {formatSpeed(job.speed_bytes_sec ?? 0)} · {formatEta(job.eta_seconds)}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleCancel(job.model_id)}
                      aria-label={`Cancel download of ${job.model_id}`}
                    >
                      Cancel
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Queued */}
      {queued.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Queued ({queued.length})
          </h3>
          <div className="space-y-1">
            {queued.map(job => (
              <Card key={job.job_id} className="p-3 flex items-center gap-3">
                <StatusDot color="muted" />
                <span className="text-sm text-text-primary font-mono flex-1 truncate">
                  {job.model_id}
                </span>
                <span className="text-xs text-text-muted">
                  Position: #{job.queue_position ?? "?"}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleCancel(job.model_id)}
                >
                  Cancel
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Completed */}
      {completed.length > 0 && (
        <div>
          <button
            onClick={() => setShowCompleted(!showCompleted)}
            className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-3"
          >
            Completed ({completed.length})
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className={`text-text-muted transition-transform duration-150 ${showCompleted ? "rotate-90" : ""}`}
            >
              <path d="M4 2l4 4-4 4" />
            </svg>
          </button>
          {showCompleted && (
            <div className="space-y-1">
              {completed.map(job => (
                <div key={job.job_id} className="flex items-center gap-3 px-3 py-2 text-sm">
                  <StatusDot color="success" />
                  <span className="text-text-primary font-mono flex-1 truncate">
                    {job.model_id}
                  </span>
                  <span className="text-xs text-text-muted">
                    {formatBytes(job.total_bytes)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Failed */}
      {failed.length > 0 && (
        <div>
          <button
            onClick={() => setShowFailed(!showFailed)}
            className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-3"
          >
            Failed ({failed.length})
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className={`text-text-muted transition-transform duration-150 ${showFailed ? "rotate-90" : ""}`}
            >
              <path d="M4 2l4 4-4 4" />
            </svg>
          </button>
          {showFailed && (
            <div className="space-y-1">
              {failed.map(job => (
                <Card key={job.job_id} className="p-3 flex items-center gap-3">
                  <StatusDot color="danger" />
                  <span className="text-sm text-text-primary font-mono flex-1 truncate">
                    {job.model_id}
                  </span>
                  <span className="text-xs text-danger max-w-[200px] truncate">
                    {job.error ?? "Unknown error"}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRetry(job.model_id)}
                  >
                    Retry
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/models/components/DownloadsView.tsx
git commit -m "feat(models): add DownloadsView with queue and progress tracking"
```

---

### Task 8: Create InstalledView Component

**Files:**
- Create: `frontend/src/features/models/components/InstalledView.tsx`

**Interfaces:**
- Consumes: `downloads.installed()`, `downloads.syncInstalled()`, `downloads.remove()`, `setDefaultModel()`, `getDefaultModel()`
- Produces: `<InstalledView />` — installed models grid with sync/delete/set-default

- [ ] **Step 1: Create InstalledView component**

```tsx
// frontend/src/features/models/components/InstalledView.tsx

"use client";

import { useState, useEffect } from "react";
import type { InstalledModel } from "../api";
import { downloads, setDefaultModel, getDefaultModel, formatBytes, formatParamCount } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { EmptyState } from "@/shared/ui/EmptyState";

interface InstalledViewProps {
  onViewDetail: (modelId: string) => void;
}

export function InstalledView({ onViewDetail }: InstalledViewProps) {
  const [models, setModels] = useState<InstalledModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [defaultModelId, setDefaultModelId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<InstalledModel | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await downloads.installed();
      setModels(res.models);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    setDefaultModelId(getDefaultModel());
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await downloads.syncInstalled();
      await load();
    } catch {
      // ignore
    } finally {
      setSyncing(false);
    }
  };

  const handleSetDefault = (modelId: string) => {
    setDefaultModel(modelId);
    setDefaultModelId(modelId);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await downloads.remove(deleteTarget.model_id);
      setModels(prev => prev.filter(m => m.model_id !== deleteTarget.model_id));
      if (defaultModelId === deleteTarget.model_id) {
        setDefaultModelId(null);
        localStorage.removeItem("cortex_default_model");
      }
      setDeleteTarget(null);
    } catch {
      // ignore
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="p-4 animate-pulse">
            <div className="space-y-3">
              <div className="h-5 w-3/4 rounded bg-bg-surface" />
              <div className="h-4 w-1/2 rounded bg-bg-surface" />
              <div className="h-3 w-1/3 rounded bg-bg-surface" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <EmptyState
        title="No models installed"
        description="Browse the catalog to download your first model"
      />
    );
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-secondary">
          {models.length} model{models.length !== 1 ? "s" : ""} installed
        </p>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleSync}
          disabled={syncing}
        >
          {syncing ? "Syncing..." : "Sync from Ollama"}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {models.map(model => {
          const isDefault = model.model_id === defaultModelId;
          const primaryVariant = model.variants?.[0];

          return (
            <Card key={model.model_id} className="p-4 flex flex-col gap-3" role="article" aria-label={model.display_name}>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-title font-semibold text-text-primary leading-tight">
                  {model.display_name}
                </h3>
                {isDefault && <Badge variant="success">Default</Badge>}
              </div>

              <p className="text-xs text-text-muted">
                {formatParamCount(model.parameter_count)} · {primaryVariant ? formatBytes(primaryVariant.size_bytes) : "?"} · {primaryVariant?.quantization ?? "?"}
              </p>

              <div className="flex items-center gap-1.5 flex-wrap">
                {model.capabilities?.map((cap) => (
                  <Badge key={cap} variant="default">{cap}</Badge>
                ))}
              </div>

              <div className="flex items-center gap-2 mt-auto pt-1">
                {!isDefault && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleSetDefault(model.model_id)}
                  >
                    Set as Default
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onViewDetail(model.model_id)}
                >
                  View Details
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="ml-auto text-danger hover:text-danger"
                  onClick={() => setDeleteTarget(model)}
                  aria-label={`Delete ${model.display_name}`}
                >
                  Delete
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Delete confirmation */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Model"
      >
        <p className="text-sm text-text-secondary mb-4">
          Delete <span className="font-mono text-text-primary">{deleteTarget?.display_name}</span>? This will remove it from Ollama.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            disabled={deleting}
            className="bg-danger hover:bg-danger/80"
          >
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </Modal>
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/models/components/InstalledView.tsx
git commit -m "feat(models): add InstalledView with sync and delete"
```

---

### Task 9: Create VariantPicker + ModelDetailModal

**Files:**
- Create: `frontend/src/features/models/components/VariantPicker.tsx`
- Create: `frontend/src/features/models/components/ModelDetailModal.tsx`

**Interfaces:**
- Consumes: `catalog.detail()`, `catalog.inferenceConfig()`, `downloads.download()`
- Produces: `<VariantPicker />`, `<ModelDetailModal />`

- [ ] **Step 1: Create VariantPicker component**

```tsx
// frontend/src/features/models/components/VariantPicker.tsx

"use client";

import { formatBytes } from "../api";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";

interface Variant {
  variant_id: string;
  quantization: string;
  size_bytes: number | null;
  size_gb: number | null;
  downloaded: boolean;
  quality_score: number | null;
  vram_required_gb?: number | null;
}

interface VariantPickerProps {
  variants: Variant[];
  onSelect: (variantId: string) => void;
  onCancel: () => void;
}

export function VariantPicker({ variants, onSelect, onCancel }: VariantPickerProps) {
  // Sort by size ascending (smallest first)
  const sorted = [...variants].sort((a, b) => (a.size_bytes ?? 0) - (b.size_bytes ?? 0));

  return (
    <div className="space-y-3">
      <p className="text-xs text-text-muted">Select a variant to download:</p>
      <div className="space-y-1.5">
        {sorted.map(v => (
          <div
            key={v.variant_id}
            className="flex items-center gap-3 px-3 py-2 rounded-lg border border-border-subtle hover:bg-bg-hover transition-colors duration-150"
          >
            <span className="text-sm text-text-primary font-mono flex-1">
              {v.quantization}
            </span>
            <span className="text-xs text-text-muted">
              {formatBytes(v.size_bytes ?? 0)}
            </span>
            {v.quality_score !== null && (
              <Badge variant="default">
                {Math.round(v.quality_score)}% quality
              </Badge>
            )}
            {v.downloaded ? (
              <Badge variant="success">Installed</Badge>
            ) : (
              <Button
                size="sm"
                onClick={() => onSelect(v.variant_id)}
                aria-label={`Download ${v.quantization} variant`}
              >
                Download
              </Button>
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-end">
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create ModelDetailModal component**

```tsx
// frontend/src/features/models/components/ModelDetailModal.tsx

"use client";

import { useState, useEffect } from "react";
import type { HardwareInfo } from "../api";
import { catalog, downloads, getDefaultModel, setDefaultModel, formatBytes, formatParamCount } from "../api";
import { Modal } from "@/shared/ui/Modal";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { VariantPicker } from "./VariantPicker";

interface ModelDetailModalProps {
  modelId: string | null;
  onClose: () => void;
  hardware: HardwareInfo | null;
  onDownloadStart: (modelName: string) => void;
}

interface ModelDetail {
  name: string;
  display_name: string;
  parameter_count: number | null;
  context_length: number | null;
  capabilities: string[];
  license: string | null;
  description: string | null;
  tags: string[];
  variants: {
    variant_id: string;
    quantization: string;
    size_bytes: number | null;
    size_gb: number | null;
    downloaded: boolean;
    quality_score: number | null;
    vram_required_gb: number | null;
  }[];
  architecture?: string;
}

interface InferenceConfig {
  temperature: number;
  top_p: number;
  top_k: number;
  repeat_penalty: number;
  num_predict: number;
  num_ctx?: number;
}

export function ModelDetailModal({
  modelId,
  onClose,
  hardware,
  onDownloadStart,
}: ModelDetailModalProps) {
  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [inference, setInference] = useState<InferenceConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [showVariantPicker, setShowVariantPicker] = useState(false);

  useEffect(() => {
    if (!modelId) return;
    setLoading(true);
    setDetail(null);
    setInference(null);
    setShowVariantPicker(false);

    Promise.all([
      catalog.detail(modelId),
      catalog.inferenceConfig(modelId),
    ])
      .then(([d, inf]) => {
        setDetail(d as ModelDetail);
        setInference(inf as InferenceConfig);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [modelId]);

  const handleDownloadVariant = async (variantId: string) => {
    if (!detail) return;
    try {
      await downloads.download(detail.name, variantId);
      onDownloadStart(detail.name);
      setShowVariantPicker(false);
      onClose();
    } catch {
      // ignore
    }
  };

  const handleUseInChat = () => {
    if (!detail) return;
    setDefaultModel(detail.name);
    window.location.href = "/chat";
  };

  const defaultVariant = detail?.variants?.find(v => !v.downloaded) ?? detail?.variants?.[0];

  return (
    <Modal open={!!modelId} onClose={onClose} title={detail?.display_name ?? "Loading..."} className="max-w-2xl">
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </div>
      ) : detail ? (
        <div className="space-y-5">
          {/* Meta row */}
          <div className="flex items-center gap-3 flex-wrap">
            {detail.parameter_count && (
              <span className="text-sm text-text-secondary font-mono">
                {formatParamCount(detail.parameter_count)} params
              </span>
            )}
            {detail.context_length && (
              <span className="text-sm text-text-muted">
                · Context: {detail.context_length} tokens
              </span>
            )}
            {detail.license && (
              <span className="text-sm text-text-muted">
                · License: {detail.license}
              </span>
            )}
          </div>

          {/* Capabilities */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {detail.capabilities.map(cap => (
              <Badge key={cap} variant="default">{cap}</Badge>
            ))}
          </div>

          {/* Description */}
          {detail.description && (
            <div>
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
                Description
              </h4>
              <p className="text-sm text-text-secondary leading-relaxed">
                {detail.description}
              </p>
            </div>
          )}

          {/* Tags */}
          {detail.tags.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
                Tags
              </h4>
              <div className="flex items-center gap-1.5 flex-wrap">
                {detail.tags.map(tag => (
                  <Badge key={tag} variant="default">{tag}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Variants */}
          <div>
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              Variants
            </h4>
            {showVariantPicker ? (
              <VariantPicker
                variants={detail.variants}
                onSelect={handleDownloadVariant}
                onCancel={() => setShowVariantPicker(false)}
              />
            ) : (
              <div className="space-y-1">
                {detail.variants.map(v => (
                  <div
                    key={v.variant_id}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg border border-border-subtle"
                  >
                    <span className="text-sm text-text-primary font-mono flex-1">
                      {v.quantization}
                    </span>
                    <span className="text-xs text-text-muted">
                      {formatBytes(v.size_bytes ?? 0)}
                    </span>
                    {v.vram_required_gb && (
                      <span className="text-xs text-text-muted">
                        {v.vram_required_gb}GB VRAM
                      </span>
                    )}
                    {v.quality_score !== null && (
                      <Badge variant="default">
                        {Math.round(v.quality_score)}%
                      </Badge>
                    )}
                    {v.downloaded ? (
                      <Badge variant="success">Installed</Badge>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleDownloadVariant(v.variant_id)}
                        aria-label={`Download ${v.quantization} variant`}
                      >
                        Download
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Inference config */}
          {inference && (
            <div>
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
                Default Inference Config
              </h4>
              <p className="text-xs text-text-muted font-mono">
                Temperature: {inference.temperature} · Top P: {inference.top_p} · Top K: {inference.top_k}
                · Repeat Penalty: {inference.repeat_penalty} · Max Tokens: {inference.num_predict}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t border-border-subtle">
            {defaultVariant && !defaultVariant.downloaded && (
              <Button
                onClick={() => handleDownloadVariant(defaultVariant.variant_id)}
              >
                Download Default Variant
              </Button>
            )}
            <Button variant="ghost" onClick={handleUseInChat}>
              Use in Chat
            </Button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-text-muted">Model not found</p>
      )}
    </Modal>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/VariantPicker.tsx frontend/src/features/models/components/ModelDetailModal.tsx
git commit -m "feat(models): add VariantPicker and ModelDetailModal"
```

---

### Task 10: Create Models Page (main component + route)

**Files:**
- Create: `frontend/src/features/models/page.tsx`
- Create: `frontend/src/app/models/page.tsx`

**Interfaces:**
- Consumes: All components from Tasks 3-9, `HardwareBar`, `BrowseView`, `CompareView`, `DownloadsView`, `InstalledView`, `ModelDetailModal`
- Produces: Complete `/models` page with 4 tabs

- [ ] **Step 1: Create the main ModelsPage component**

```tsx
// frontend/src/features/models/page.tsx

"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Button } from "@/shared/ui/Button";
import { HardwareBar } from "./components/HardwareBar";
import { BrowseView } from "./components/BrowseView";
import { CompareView } from "./components/CompareView";
import { DownloadsView } from "./components/DownloadsView";
import { InstalledView } from "./components/InstalledView";
import { ModelDetailModal } from "./components/ModelDetailModal";
import { catalog, downloads, getDefaultModel } from "./api";
import type { HardwareInfo, TabKey } from "./api";

const tabs: { key: TabKey; label: string }[] = [
  { key: "browse", label: "Browse" },
  { key: "compare", label: "Compare" },
  { key: "downloads", label: "Downloads" },
  { key: "installed", label: "Installed" },
];

export default function ModelsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<TabKey>("browse");
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [hardwareLoading, setHardwareLoading] = useState(true);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [detailModelId, setDetailModelId] = useState<string | null>(null);
  const [downloadingModels, setDownloadingModels] = useState<Map<string, number>>(new Map());

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  // Load hardware once
  useEffect(() => {
    catalog
      .hardware()
      .then(setHardware)
      .catch(() => setHardware(null))
      .finally(() => setHardwareLoading(false));
  }, []);

  const handleToggleCompare = useCallback((modelId: string) => {
    setCompareIds(prev =>
      prev.includes(modelId) ? prev.filter(id => id !== modelId) : [...prev, modelId]
    );
  }, []);

  const handleDownload = useCallback(async (modelId: string) => {
    try {
      await downloads.download(modelId);
      setDownloadingModels(prev => new Map(prev).set(modelId, 0));
      // Start polling this model's progress
      const poll = setInterval(async () => {
        try {
          const res = await downloads.progress(modelId);
          if (res.progress >= 1) {
            clearInterval(poll);
            setDownloadingModels(prev => {
              const next = new Map(prev);
              next.delete(modelId);
              return next;
            });
          } else {
            setDownloadingModels(prev => new Map(prev).set(modelId, res.progress));
          }
        } catch {
          clearInterval(poll);
          setDownloadingModels(prev => {
            const next = new Map(prev);
            next.delete(modelId);
            return next;
          });
        }
      }, 2000);
    } catch {
      // ignore
    }
  }, []);

  const handleCancelDownload = useCallback(async (modelId: string) => {
    try {
      await downloads.cancel(modelId);
      setDownloadingModels(prev => {
        const next = new Map(prev);
        next.delete(modelId);
        return next;
      });
    } catch {
      // ignore
    }
  }, []);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-6xl space-y-4">
        {/* Header */}
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Models</h1>
          <p className="text-sm text-text-secondary mt-1">
            Browse, download, and manage LLMs
          </p>
        </div>

        {/* Hardware bar */}
        <HardwareBar hardware={hardware} loading={hardwareLoading} />

        {/* Tab bar */}
        <div className="flex items-center gap-1 border-b border-border-subtle overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors duration-150 ${
                activeTab === tab.key
                  ? "border-b-2 border-accent text-accent"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {tab.label}
              {tab.key === "compare" && compareIds.length > 0 && (
                <span className="ml-1.5 text-xs text-text-muted">
                  ({compareIds.length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === "browse" && (
          <BrowseView
            hardware={hardware}
            onDownload={handleDownload}
            onViewDetail={setDetailModelId}
            compareSelectedIds={compareIds}
            onToggleCompare={handleToggleCompare}
            compareDisabled={compareIds.length >= 5}
            downloadingModels={downloadingModels}
            onCancelDownload={handleCancelDownload}
          />
        )}

        {activeTab === "compare" && (
          <CompareView
            selectedIds={compareIds}
            onClearSelection={() => setCompareIds([])}
            onDownloadModel={handleDownload}
          />
        )}

        {activeTab === "downloads" && <DownloadsView />}

        {activeTab === "installed" && (
          <InstalledView onViewDetail={setDetailModelId} />
        )}

        {/* Floating compare button */}
        {activeTab === "browse" && compareIds.length >= 2 && (
          <div className="fixed bottom-6 right-6 z-toast">
            <Button onClick={() => setActiveTab("compare")}>
              Compare {compareIds.length} models
            </Button>
          </div>
        )}

        {/* Model detail modal */}
        <ModelDetailModal
          modelId={detailModelId}
          onClose={() => setDetailModelId(null)}
          hardware={hardware}
          onDownloadStart={handleDownload}
        />
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 2: Create the route page (re-export)**

```tsx
// frontend/src/app/models/page.tsx

export { default } from "@/features/models/page";
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30`
Expected: No new TypeScript errors from models/* files.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/models/page.tsx frontend/src/app/models/page.tsx
git commit -m "feat(models): add /models page with Browse, Compare, Downloads, Installed tabs"
```

---

### Task 11: Update Sidebar Navigation

**Files:**
- Modify: `frontend/src/shared/layout/Sidebar.tsx`

**Interfaces:**
- Consumes: Nothing new
- Produces: Updated sidebar with "Models" nav link between Agents and System

- [ ] **Step 1: Add Models to navigation array and icon map**

```typescript
// In Sidebar.tsx, update the navigation array:
const navigation = [
  { name: "Dashboard", href: "/", icon: "grid" },
  { name: "Chat", href: "/chat", icon: "message" },
  { name: "Agents", href: "/agents", icon: "cpu" },
  { name: "Models", href: "/models", icon: "download" },
  { name: "System", href: "/system", icon: "activity" },
  { name: "Settings", href: "/settings", icon: "settings" },
] as const;
```

Add the download icon to iconMap:

```typescript
download: (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M9 2v10M5 8l4 4 4-4M3 14h12" />
  </svg>
),
```

- [ ] **Step 2: Verify the page renders**

Run: `cd frontend && npm run build 2>&1 | tail -20`
Expected: Build succeeds. Navigate to `http://localhost:3000/models` and verify the page loads.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/layout/Sidebar.tsx
git commit -m "feat(models): add Models link to sidebar navigation"
```

---

### Task 12: Add Model Selector to Chat Page

**Files:**
- Modify: `frontend/src/features/chat/page.tsx`

**Interfaces:**
- Consumes: `downloads.installed()`, `getDefaultModel()`, `setDefaultModel()` from `models/api.ts`
- Produces: Model selector dropdown in chat header, model_id passed to streamChat

- [ ] **Step 1: Add model selector to ChatPage**

Add these imports at the top:

```typescript
import { useState as useStateModels, useEffect as useEffectModels } from "react";
import { downloads as modelsDownloads, getDefaultModel, setDefaultModel } from "@/features/models/api";
import type { InstalledModel } from "@/features/models/api";
```

Add model state inside ChatPage component (after existing state declarations):

```typescript
// Model selector state
const [installedModels, setInstalledModels] = useStateModels<InstalledModel[]>([]);
const [selectedModel, setSelectedModel] = useStateModels<string | null>(null);

useEffectModels(() => {
  modelsDownloads
    .installed()
    .then((res) => {
      setInstalledModels(res.models);
      const saved = getDefaultModel();
      if (saved) {
        setSelectedModel(saved);
      } else if (res.models.length > 0) {
        setSelectedModel(res.models[0].model_id);
      }
    })
    .catch(() => {});
}, []);
```

Add model selector UI in the chat area header — inside the `{/* Chat area */}` div, right before the messages section, add a model bar:

```tsx
{/* Model selector bar */}
{activeId && (
  <div className="flex items-center gap-3 px-6 py-2 border-b border-border-subtle bg-bg-elevated">
    <span className="text-xs text-text-muted">Model:</span>
    <select
      value={selectedModel ?? ""}
      onChange={(e) => {
        setSelectedModel(e.target.value);
        setDefaultModel(e.target.value);
      }}
      className="h-7 rounded-md border border-border-default bg-bg-surface px-2 text-xs text-text-secondary focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none"
      aria-label="Select model"
    >
      {installedModels.map((m) => (
        <option key={m.model_id} value={m.model_id}>
          {m.display_name}
        </option>
      ))}
    </select>
    <a
      href="/models"
      className="text-xs text-accent hover:text-accent-hover transition-colors duration-150"
    >
      Browse →
    </a>
  </div>
)}
```

Update `handleSend` to pass the selected model:

```typescript
for await (const event of streamChat(convId, content, selectedModel ?? undefined)) {
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/chat/page.tsx
git commit -m "feat(chat): add model selector dropdown to chat page"
```

---

### Task 13: Final Build + Validation

**Files:** None created — validation only.

- [ ] **Step 1: Full TypeScript check**

Run: `cd frontend && npx tsc --noEmit --pretty 2>&1`

- [ ] **Step 2: Full build**

Run: `cd frontend && npm run build 2>&1 | tail -30`

- [ ] **Step 3: Verify no forbidden patterns**

Run:
```bash
grep -rn 'transition-all\|h-screen\|glassmorphism\|gradient.*text' frontend/src/features/models/ --include='*.tsx' --include='*.ts' 2>/dev/null
```
Expected: No matches.

- [ ] **Step 4: Verify all 16 backend endpoints are consumed**

Run:
```bash
grep -rn '/models/' frontend/src/features/models/ frontend/src/features/developer/api.ts frontend/src/features/integration/api.ts --include='*.ts' --include='*.tsx' | grep -v node_modules | grep -v '.next'
```
Expected: All 16 endpoints referenced.

- [ ] **Step 5: Commit any fixes**

If any issues found, fix and commit.

---

## Summary

| Task | What It Builds | Files |
|------|---------------|-------|
| 1 | Fix API client URL paths | 2 modified |
| 2 | Merged API client + types | 1 created |
| 3 | HardwareBar component | 1 created |
| 4 | ModelCard component | 1 created |
| 5 | BrowseView component | 1 created |
| 6 | CompareView component | 1 created |
| 7 | DownloadsView component | 1 created |
| 8 | InstalledView component | 1 created |
| 9 | VariantPicker + ModelDetailModal | 2 created |
| 10 | Models page (main + route) | 2 created |
| 11 | Sidebar navigation update | 1 modified |
| 12 | Chat model selector | 1 modified |
| 13 | Final validation | 0 |
| **Total** | | **11 created, 4 modified** |

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-28-model-catalog.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
