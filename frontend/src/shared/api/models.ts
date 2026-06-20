/**
 * Models API client — catalog, hardware detection, download, and health.
 */

import { api } from "./client";
import type {
  ModelListResponse,
  RecommendedModelsResponse,
  RecommendedModelsResponseEnhanced,
  HardwareInfo,
  DownloadProgressResponse,
  DownloadResult,
  DownloadJob,
  DownloadQueueResponse,
  StorageUsage,
  ModelCatalogEntry,
} from "../types";

export const modelsApi = {
  /** List all models from catalog and available providers. */
  list: (params: {
    model_type?: string;
    downloaded_only?: boolean;
  } = {}): Promise<ModelListResponse> => {
    const query = new URLSearchParams();
    if (params.model_type) query.set("model_type", params.model_type);
    if (params.downloaded_only) query.set("downloaded_only", "true");
    const qs = query.toString();
    return api.get(`/api/v1/models${qs ? `?${qs}` : ""}`);
  },

  /** Get hardware-appropriate model recommendations. */
  recommended: (): Promise<RecommendedModelsResponse> => {
    return api.get("/api/v1/models/recommended");
  },

  /** Detect system hardware (RAM, CPU, GPU). */
  hardware: (): Promise<HardwareInfo> => {
    return api.get("/api/v1/models/hardware");
  },

  /** Check health of all LLM providers. */
  health: (): Promise<Record<string, unknown>> => {
    return api.get("/api/v1/models/health");
  },

  /** Get token usage and request metrics. */
  metrics: (): Promise<Record<string, unknown>> => {
    return api.get("/api/v1/models/metrics");
  },

  /** Start downloading a model. */
  download: (modelName: string, variant?: string): Promise<DownloadResult> => {
    const params = variant ? `?variant=${encodeURIComponent(variant)}` : "";
    return api.post(`/api/v1/models/${encodeURIComponent(modelName)}/download${params}`);
  },

  /** Get download progress for a model. */
  progress: (modelName: string): Promise<DownloadProgressResponse> => {
    return api.get(`/api/v1/models/${encodeURIComponent(modelName)}/progress`);
  },

  /** Cancel an active download. */
  cancel: (modelName: string): Promise<{ cancelled: boolean }> => {
    return api.post(`/api/v1/models/${encodeURIComponent(modelName)}/cancel`);
  },

  /** Get per-workload recommendations. */
  recommendedEnhanced: (workload?: string): Promise<RecommendedModelsResponseEnhanced> => {
    const qs = workload ? `?workload=${encodeURIComponent(workload)}` : "";
    return api.get(`/api/v1/models/recommended${qs}`);
  },

  /** Get installed models with status. */
  installed: (): Promise<{ models: ModelCatalogEntry[]; installed_count: number }> => {
    return api.get("/api/v1/models/installed");
  },

  /** Get download queue. */
  downloadQueue: (): Promise<DownloadQueueResponse> => {
    return api.get("/api/v1/models/downloads/queue");
  },

  /** Get download history. */
  downloadHistory: (limit?: number): Promise<{ history: DownloadJob[] }> => {
    const qs = limit ? `?limit=${limit}` : "";
    return api.get(`/api/v1/models/downloads/history${qs}`);
  },

  /** Get storage usage. */
  storage: (): Promise<StorageUsage> => {
    return api.get("/api/v1/models/storage");
  },

  /** Refresh catalogue. */
  refreshCatalogue: (): Promise<{ status: string; models_added: number }> => {
    return api.post("/api/v1/models/catalogue/refresh");
  },

  /** Get model detail with variants. */
  detail: (modelId: string): Promise<ModelCatalogEntry> => {
    return api.get(`/api/v1/models/${encodeURIComponent(modelId)}`);
  },

  /** Get inference config for a model. */
  inferenceConfig: (modelId: string): Promise<Record<string, unknown>> => {
    return api.get(`/api/v1/models/${encodeURIComponent(modelId)}/inference-config`);
  },

  /** Check for model updates. */
  checkUpdates: (): Promise<{ updates: Array<{ model_id: string; current: string; latest: string }> }> => {
    return api.get("/api/v1/models/updates");
  },
};
