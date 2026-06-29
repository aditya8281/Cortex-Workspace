/**
 * Integration API Client — aligned with backend v1 integration endpoints
 *
 * Covers: Downloads & Sync
 * Backend routes: /api/v1/models/*, /api/v1/sync/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types (matching backend Pydantic schemas) ──────────────────────────────

// Backend: InstalledVariant
export interface InstalledVariant {
  variant_id: string;
  quantization: string;
  size_bytes: number;
  size_gb: number;
  downloaded: boolean;
  parameter_count: number | null;
  quality_score: number;
}

// Backend: InstalledModel
export interface InstalledModel {
  model_id: string;
  display_name: string;
  family: string;
  parameter_count: number | null;
  capabilities: string[];
  variants: InstalledVariant[];
}

// Backend: DownloadJobInfo
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

// Backend: DownloadHistoryItem (timestamps are unix floats)
export interface DownloadHistoryItem {
  job_id: string;
  model_id: string;
  status: string;
  progress: number;
  downloaded_bytes: number;
  total_bytes: number;
  error: string | null;
  completed_at: number | null;
  created_at: number | null;
}

// Backend: SyncJobResponse
export interface SyncJob {
  job_id: string;
  repo_path: string;
  status: string;
  file_count: number;
  last_sync: string | null;
  error_message: string | null;
}

// Backend: SyncDefaultsResponse
export interface SyncDefaults {
  default_paths: Array<{ name: string; path: string; type: string }>;
  exclude_dirs: string[];
  embedding_models: Array<{ name: string; dimension: number }>;
}

// Backend: SyncStatusResponse
export interface SyncStatus {
  watching: number;
  pending_changes: number;
  indexed_files: number;
  errors: number;
  status: string;
  last_sync: string | null;
  watched_paths: Array<{ path: string; status: string }>;
}

// Backend: SyncStartResponse
export interface SyncStartResult {
  status: string;
  repo_path: string;
  embedding_model: string;
  initial_scan_job_id: string | null;
}

// Backend: SyncStopResponse
export interface SyncStopResult {
  status: string;
  repo_path: string;
}

// Backend: SyncValidatePathResponse
export interface SyncValidatePathResult {
  path: string;
  resolved_path: string;
  exists: boolean;
}

// ── Sync ───────────────────────────────────────────────────────────────────

export const sync = {
  defaults: () =>
    apiFetch<SyncDefaults>("/sync/defaults"),

  start: (data: { repo_path: string; embedding_model?: string; exclude_dirs?: string[]; exclude_patterns?: string[] }) =>
    apiFetch<SyncStartResult>("/sync/start", { method: "POST", body: data }),

  validatePath: (data: { path: string }) =>
    apiFetch<SyncValidatePathResult>("/sync/validate-path", { method: "POST", body: data }),

  stop: (data: { repo_path: string }) =>
    apiFetch<SyncStopResult>("/sync/stop", { method: "POST", body: data }),

  status: () =>
    apiFetch<SyncStatus>("/sync/status"),

  jobs: () =>
    apiFetch<SyncJob[]>("/sync/jobs"),

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
      { method: "POST" },
    ),

  progress: (modelName: string) =>
    apiFetch<{ model: string; progress: number }>(`/models/${modelName}/progress`),

  cancel: (modelName: string) =>
    apiFetch<{ cancelled: boolean }>(`/models/${modelName}/cancel`, { method: "POST" }),

  remove: (modelName: string) =>
    apiFetch<{ status: string; model: string }>(`/models/${modelName}`, { method: "DELETE" }),

  pause: (jobId: string) =>
    apiFetch<{ paused: boolean; model: string }>(
      `/models/downloads/${jobId}/pause`,
      { method: "POST" },
    ),

  resume: (jobId: string) =>
    apiFetch<{ resumed: boolean; model: string }>(
      `/models/downloads/${jobId}/resume`,
      { method: "POST" },
    ),

  deleteLocal: (modelName: string) =>
    apiFetch<{ status: string; model: string }>(
      `/models/${modelName}/local`,
      { method: "DELETE" },
    ),

  reorder: (jobIds: string[]) =>
    apiFetch<{ reordered: boolean; new_order: string[] }>(
      "/models/downloads/reorder",
      { method: "POST", body: { job_ids: jobIds } },
    ),

  bulkCancel: (jobIds: string[]) =>
    apiFetch<{ cancelled: number; job_ids: string[] }>(
      "/models/downloads/bulk-cancel",
      { method: "POST", body: { job_ids: jobIds } },
    ),

  clearCompleted: () =>
    apiFetch<{ cleared: number }>(
      "/models/downloads/clear-completed",
      { method: "POST" },
    ),
};
