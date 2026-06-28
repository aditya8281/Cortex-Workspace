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
