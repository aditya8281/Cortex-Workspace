/**
 * Intelligence API Client — Models & Model Management
 *
 * Backend routes: /api/v1/models/*
 * Catalog: developer/catalog.py, Downloads: integration/downloads.py
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface Model {
  id: string;
  name: string;
  provider: string;
  description: string;
  context_length: number;
  is_installed: boolean;
  is_default: boolean;
  capabilities: string[];
}

export interface InstalledModel {
  id: string;
  name: string;
  provider: string;
  status: "ready" | "downloading" | "error";
  size: number;
  loaded: boolean;
}

export interface DownloadQueueItem {
  id: string;
  model_name: string;
  status: "queued" | "downloading" | "completed" | "failed" | "cancelled";
  progress: number;
  speed: number;
  eta: number;
}

export interface DownloadHistoryItem {
  model_name: string;
  downloaded_at: string;
  size: number;
  status: "success" | "failed";
}

// ── Models ─────────────────────────────────────────────────────────────────

export const models = {
  list: () =>
    apiFetch<{ items: Model[] }>("/models"),

  installed: () =>
    apiFetch<{ items: InstalledModel[] }>("/models/installed"),

  syncInstalled: () =>
    apiFetch<{ synced: boolean }>("/models/installed/sync", { method: "POST" }),

  downloadQueue: () =>
    apiFetch<{ items: DownloadQueueItem[] }>("/models/downloads/queue"),

  downloadHistory: () =>
    apiFetch<{ items: DownloadHistoryItem[] }>("/models/downloads/history"),

  download: (modelName: string) =>
    apiFetch<{ status: string }>(`/models/${modelName}/download`, { method: "POST" }),

  progress: (modelName: string) =>
    apiFetch<DownloadQueueItem>(`/models/${modelName}/progress`),

  cancel: (modelName: string) =>
    apiFetch<{ cancelled: boolean }>(`/models/${modelName}/cancel`, { method: "POST" }),

  remove: (modelName: string) =>
    apiFetch<{ deleted: boolean }>(`/models/${modelName}`, { method: "DELETE" }),
};
