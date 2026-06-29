/**
 * Awareness API Client — aligned with backend v1 awareness endpoints
 *
 * Covers: Device, Environment, Files, Health, Indexing, Project, Repository
 * Backend routes: /api/v1/awareness/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types (matching backend Pydantic schemas) ──────────────────────────────

export interface DeviceInfo {
  hostname: string;
  os: string;
  cpu: string;
  memory_total: number;
  memory_used: number;
  disk_total: number;
  disk_used: number;
  python_version: string;
  cortex_version: string;
}

export interface EnvironmentInfo {
  variables: Record<string, string>;
  paths: string[];
  working_directory: string;
}

export interface FileChange {
  path: string;
  change_type: "created" | "modified" | "deleted";
  timestamp: string;
  size: number;
}

export interface FileSummary {
  total_files: number;
  total_size: number;
  by_extension: Record<string, number>;
  last_scan: string;
}

export interface IndexingConfig {
  enabled: boolean;
  watched_directories: string[];
  ignore_patterns: string[];
  max_file_size: number;
}

export interface ProjectInfo {
  type: string;
  name: string;
  languages: string[];
  frameworks: string[];
  config: Record<string, any>;
}

// Backend RepoInfo from schemas/developer/repository.py
export interface RepoInfo {
  id: number;
  user_id: number;
  repo_path: string;
  repo_name: string;
  primary_language: string | null;
  total_files: number;
  total_chunks: number;
  last_indexed_at: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

// Backend RepoListResponse
export interface RepoListResponse {
  repos: RepoInfo[];
}

// Backend RepoIndexStatusResponse
export interface RepoIndexStatus {
  repo_id: number;
  status: string;
  total_files: number;
  total_chunks: number;
  indexed_files: number;
  indexed: number;
  pending: number;
  errors: number;
  last_indexed_at: string | null;
}

// Backend GraphBuildResponse
export interface GraphBuildResult {
  status: string;
  nodes_created: number;
  edges_created: number;
}

// Backend GraphGetResponse
export interface GraphData {
  nodes: any[];
  edges: any[];
}

// Backend NodeContextResponse
export interface NodeContext {
  node_id: number;
  label: string;
  node_type: string;
  neighbors: any[];
}

// Backend awareness health response (dict[str, Any])
export interface AwarenessHealth {
  services: Array<{
    id: number;
    service_name: string;
    status: string;
    response_time_ms: number | null;
    error_message: string | null;
    last_check: string | null;
  }>;
  overall_status: string;
  summary: Record<string, any>;
}

// Backend scan response
export interface ScanResult {
  id: number;
  repo_path: string;
  repo_name: string;
  languages: string[];
  total_files: number;
  total_lines: number;
  framework: string | null;
  dependencies: string[];
  git_branch: string;
  last_commit_hash: string;
  last_indexed: string | null;
}

// ── Device ─────────────────────────────────────────────────────────────────

export const device = {
  info: () =>
    apiFetch<DeviceInfo>("/awareness/device/info"),
};

// ── Environment ────────────────────────────────────────────────────────────

export const environment = {
  info: () =>
    apiFetch<EnvironmentInfo>("/awareness/environment"),

  paths: () =>
    apiFetch<{ paths: string[] }>("/awareness/environment/paths"),
};

// ── Files ──────────────────────────────────────────────────────────────────

export const files = {
  scan: (directory: string) => {
    const qs = `?directory=${encodeURIComponent(directory)}`;
    return apiFetch<{ files_indexed: number; stats: Record<string, any>; directory: string }>(`/awareness/files/scan${qs}`, { method: "POST" });
  },

  changes: (directory: string) => {
    const qs = `?directory=${encodeURIComponent(directory)}`;
    return apiFetch<{ created: number; modified: number; deleted: number }>(`/awareness/files/changes${qs}`);
  },

  summary: (directory: string) => {
    const qs = `?directory=${encodeURIComponent(directory)}`;
    return apiFetch<FileSummary>(`/awareness/files/summary${qs}`);
  },
};

// ── Health ─────────────────────────────────────────────────────────────────

export const awarenessHealth = {
  check: () =>
    apiFetch<AwarenessHealth>("/awareness/health"),

  status: () =>
    apiFetch<{ status: string; details: any }>("/awareness/health/status"),
};

// ── Indexing ───────────────────────────────────────────────────────────────

export const indexing = {
  config: () =>
    apiFetch<IndexingConfig>("/awareness/indexing/config"),

  saveConfig: (data: Partial<IndexingConfig>) =>
    apiFetch<{ saved: boolean }>("/awareness/indexing/config", { method: "PUT", body: data }),

  preview: (data: { directory: string }) =>
    apiFetch<{ files: string[]; total: number; estimated_time: number }>("/awareness/indexing/preview", { method: "POST", body: data }),
};

// ── Project ────────────────────────────────────────────────────────────────

export const project = {
  scan: () =>
    apiFetch<ProjectInfo>("/awareness/project/scan"),
};

// ── Repository ─────────────────────────────────────────────────────────────

export const repository = {
  list: () =>
    apiFetch<RepoListResponse>("/awareness/repos"),

  create: (data: { name: string; path: string }) =>
    apiFetch<{ status: string; repo: RepoInfo }>("/awareness/repos", { method: "POST", body: data }),

  get: (id: number) =>
    apiFetch<{ repo: RepoInfo }>(`/awareness/repos/${id}`),

  update: (id: number, data: { name?: string }) =>
    apiFetch<{ status: string; repo: RepoInfo }>(`/awareness/repos/${id}`, { method: "PUT", body: data }),

  delete: (id: number) =>
    apiFetch<{ status: string }>(`/awareness/repos/${id}`, { method: "DELETE" }),

  index: (id: number, force?: boolean) => {
    const qs = force ? "?force=true" : "";
    return apiFetch<{ status: string; job_id?: string; result?: { status: string; files_scanned: number; files_indexed: number; files_skipped: number; chunks_created: number } }>(
      `/awareness/repos/${id}/index${qs}`, { method: "POST" },
    );
  },

  indexStatus: (id: number) =>
    apiFetch<RepoIndexStatus>(`/awareness/repos/${id}/status`),

  scan: (repoPath: string) => {
    const qs = `?repo_path=${encodeURIComponent(repoPath)}`;
    return apiFetch<ScanResult>(`/awareness/repos/scan${qs}`);
  },

  buildGraph: (id: number) =>
    apiFetch<GraphBuildResult>(`/awareness/repos/${id}/graph`, { method: "POST" }),

  getGraph: (id: number) =>
    apiFetch<GraphData>(`/awareness/repos/${id}/graph`),

  graphNode: (repoId: number, nodeId: number) =>
    apiFetch<NodeContext>(`/awareness/repos/${repoId}/graph/node/${nodeId}`),
};
