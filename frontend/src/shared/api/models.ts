/**
 * Models API client — catalog, hardware detection, download, and health.
 */

import { api } from "./client";
import type {
  ModelListResponse,
  RecommendedModelsResponse,
  HardwareInfo,
  DownloadProgressResponse,
  DownloadResult,
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
};
