/**
 * Awareness API Client — v1.04 Awareness Foundation
 *
 * Covers: Device, Environment, Files, Health, Indexing, Project, Repository
 * Backend routes: /api/v1/awareness/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

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

export interface RepoEntry {
  id: number;
  name: string;
  path: string;
  description: string;
  languages: string[];
  file_count: number;
  total_lines: number;
  is_indexed: boolean;
  created_at: string;
  last_indexed: string;
}

export interface AwarenessHealth {
  status: string;
  indexing_active: boolean;
  watched_count: number;
  last_scan: string;
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
    apiFetch<{ items: RepoEntry[] }>("/awareness/repos"),

  create: (data: { name: string; path: string; description?: string }) =>
    apiFetch<RepoEntry>("/awareness/repos", { method: "POST", body: data }),

  get: (id: number) =>
    apiFetch<RepoEntry>(`/awareness/repos/${id}`),

  update: (id: number, data: Partial<{ name: string; description: string }>) =>
    apiFetch<RepoEntry>(`/awareness/repos/${id}`, { method: "PUT", body: data }),

  delete: (id: number) =>
    apiFetch<void>(`/awareness/repos/${id}`, { method: "DELETE" }),

  index: (id: number) =>
    apiFetch<{ status: string }>(`/awareness/repos/${id}/index`, { method: "POST" }),

  indexStatus: (id: number) =>
    apiFetch<{ status: string; progress: number; last_indexed: string }>(`/awareness/repos/${id}/status`),

  scanAll: () =>
    apiFetch<{ scanned: number }>("/awareness/repos/scan", { method: "POST" }),

  buildGraph: (id: number) =>
    apiFetch<{ nodes: number; edges: number }>(`/awareness/repos/${id}/graph`, { method: "POST" }),

  getGraph: (id: number) =>
    apiFetch<{ nodes: any[]; edges: any[] }>(`/awareness/repos/${id}/graph`),

  graphNode: (repoId: number, nodeId: number) =>
    apiFetch<any>(`/awareness/repos/${repoId}/graph/node/${nodeId}`),
};
