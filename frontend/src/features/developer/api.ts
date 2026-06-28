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

  refresh: () =>
    apiFetch<{ status: string; message: string; total_models: number | null }>(
      "/models/refresh",
      { method: "POST" }
    ),
};
