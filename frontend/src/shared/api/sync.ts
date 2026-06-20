/**
 * Sync API client — file watcher control and status.
 */

import { api } from "./client";

export interface SyncJob {
  job_id: string;
  repo_path: string;
  job_type: string;
  status: string;
  progress: number;
  total: number | null;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface WatchedPath {
  path: string;
  repo_id: number | null;
  embedding_model: string;
  sync_enabled: boolean;
  initial_scan_job_id: string | null;
  initial_scan_status: string | null;
}

export interface SyncStatus {
  watching: number;
  pending_changes: number;
  indexed_files: number;
  errors: number;
  status: string;
  last_sync: string | null;
  watched_paths: WatchedPath[];
}

export interface SyncDefaultPath {
  label: string;
  path: string;
  enabled: boolean;
  exists: boolean;
}

export interface EmbeddingModelOption {
  value: string;
  label: string;
  technique: string;
  dimensions: number;
  description: string;
  speed: "instant" | "fast" | "medium" | "slow";
}

export interface SyncDefaults {
  default_paths: SyncDefaultPath[];
  exclude_dirs: string[];
  embedding_models: EmbeddingModelOption[];
}

export const syncApi = {
  defaults: (): Promise<SyncDefaults> => {
    return api.get("/api/v1/sync/defaults");
  },

  start: (repoPath: string, embeddingModel?: string, excludeDirs?: string[]): Promise<{
    status: string;
    repo_path: string;
    embedding_model: string;
    initial_scan_job_id: string | null;
  }> => {
    return api.post("/api/v1/sync/start", {
      repo_path: repoPath,
      embedding_model: embeddingModel,
      exclude_dirs: excludeDirs,
    });
  },

  stop: (repoPath: string): Promise<{ status: string; repo_path: string }> => {
    return api.post("/api/v1/sync/stop", { repo_path: repoPath });
  },

  status: (): Promise<SyncStatus> => {
    return api.get("/api/v1/sync/status");
  },

  jobs: (): Promise<SyncJob[]> => {
    return api.get("/api/v1/sync/jobs");
  },

  getJob: (jobId: string): Promise<SyncJob> => {
    return api.get(`/api/v1/sync/jobs/${jobId}`);
  },
};
