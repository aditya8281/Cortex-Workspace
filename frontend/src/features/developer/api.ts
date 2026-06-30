/**
 * Developer API Client — aligned with backend v1 developer endpoints
 *
 * Covers: Model Catalog, GitHub connection
 * Backend routes: /api/v1/models/*, /api/v1/me/github
 */
import { apiFetch } from "@/shared/api/client";

// ── Types (matching backend Pydantic schemas) ──────────────────────────────

// Backend: /me/github — GitHubResponse
export interface GitHubStatus {
  connected: boolean;
  github_username: string | null;
}

// Backend: ModelProviderInfo
export interface ModelProviderInfo {
  name: string;
  size_bytes: number;
  context_length: number;
  capabilities: string[];
}

// Backend: ModelCatalogEntry — simplified (variants is just strings in list endpoint)
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
  family: string | null;
  embedding_dim: number | null;
  variants: string[];
  hardware_requirements: Record<string, any>;
}

// Backend: CatalogSourceStatusResponse
export interface CatalogSourceStatus {
  cloud: string;
  local: string;
  registry: string;
  last_updated: string;
  from_fallback: boolean;
  errors: Record<string, string>;
}

// Backend: ModelListResponse
export interface ModelListResponse {
  models: ModelCatalogEntry[];
  total_count: number;
  downloaded_count: number;
  available_from_providers: ModelProviderInfo[];
  type_counts: Record<string, number>;
  size_counts: Record<string, number>;
  catalog_status: CatalogSourceStatus | null;
}

// Backend: HardwareInfoResponse
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

// Backend: RecommendationVariant
export interface RecommendationVariant {
  quantization: string | null;
  size_gb: number | null;
  vram_required_gb: number | null;
  quality_score: number | null;
}

// Backend: RecommendationPerformance
export interface RecommendationPerformance {
  tokens_per_second: number | null;
  prompt_eval_tps: number | null;
  memory_usage_gb: number | null;
  vram_usage_gb: number | null;
  quantization_quality: string | null;
  quality_notes: string | null;
  speed_rating: string | null;
  fit_rating: string | null;
  context_length_max: number | null;
}

// Backend: RecommendationExplanation
export interface RecommendationExplanation {
  why: string | null;
  tradeoff: string | null;
  suitability: string | null;
}

// Backend: ModelRecommendation
export interface ModelRecommendation {
  model_id: string;
  display_name: string;
  family: string;
  parameter_count: number | null;
  capabilities: string[];
  description: string | null;
  score: number;
  variant: RecommendationVariant | null;
  performance: RecommendationPerformance | null;
  explanation: RecommendationExplanation | null;
}

// Backend: WorkloadRecommendations
export interface WorkloadRecommendations {
  label: string;
  description: string;
  recommendations: ModelRecommendation[];
}

// Backend: RecommendedModelsAllResponse
export interface RecommendedModelsAllResponse {
  hardware: Record<string, any>;
  workloads: Record<string, WorkloadRecommendations>;
}

// Backend: ModelSearchResult
export interface ModelSearchResult {
  name: string;
  display_name: string;
  provider: string;
  model_type: string;
  size_bytes: number | null;
  context_length: number | null;
  capabilities: string[];
  description: string | null;
  tags: string[];
}

// Backend: ModelVariantInfo (for detail view)
export interface ModelVariantInfo {
  variant_id: string;
  quantization: string;
  quantization_level: string | null;
  parameter_count: number | null;
  size_bytes: number | null;
  size_gb: number | null;
  vram_required_gb: number | null;
  quality_score: number | null;
  downloaded: boolean | null;
  ollama_tag: string | null;
}

// Backend: ModelDetailResponse
export interface ModelDetail {
  model_id: string;
  display_name: string;
  family: string;
  parameter_count: number | null;
  architecture: string | null;
  context_length_default: number | null;
  context_length_max: number | null;
  capabilities: string[];
  license: string | null;
  recommended_use_cases: string[];
  description: string | null;
  tags: string[];
  downloaded: boolean;
  embedding_dim: number | null;
  benchmarks: Record<string, any> | null;
  variants: ModelVariantInfo[];
}

// Backend: DimensionComparisonResponse
export interface DimensionComparison {
  dimension: string;
  display_name: string;
  values: Record<string, number>;
  winner: string;
  higher_is_better: boolean;
}

// Backend: ModelComparisonResponse
export interface ModelComparison {
  winner_model: string;
  dimension_wins: Record<string, string>;
  dimensions: DimensionComparison[];
  summary: string;
}

// Backend: RefreshCatalogResponse
export interface RefreshCatalogResponse {
  status: string;
  message: string;
  total_models: number | null;
  source_status: CatalogSourceStatus | null;
}

// ── Family grouping ─────────────────────────────────────────────────────────

export interface FamilyVariant {
  model_id: string;
  parameter_count: number | null;
  size_gb: number | null;
  size_bytes: number | null;
  quantization: string | null;
  context_length: number | null;
  downloaded: boolean;
  license: string | null;
  embedding_dim: number | null;
}

export interface FamilySummary {
  family: string;
  display_name: string;
  model_count: number;
  capabilities: string[];
  default_variant: FamilyVariant;
  context_range: [number, number];
  param_range: [number, number];
  license: string | null;
  embedding_dim: number | null;
}

export interface ModelFamiliesResponse {
  families: FamilySummary[];
  embedding_families: FamilySummary[];
  total_families: number;
  total_models: number;
}

export interface FamilyVariantsResponse {
  family: string;
  display_name: string;
  variants: FamilyVariant[];
}

// ── GitHub ─────────────────────────────────────────────────────────────────

export const github = {
  status: () =>
    apiFetch<GitHubStatus>("/me/github"),

  connect: (data: { username: string; token: string }) =>
    apiFetch<GitHubStatus>("/me/github", { method: "POST", body: data }),

  disconnect: () =>
    apiFetch<GitHubStatus>("/me/github", { method: "DELETE" }),
};

// ── Model Catalog ──────────────────────────────────────────────────────────

export const catalog = {
  list: (params?: { model_type?: string; downloaded_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.model_type) searchParams.set("model_type", params.model_type);
    if (params?.downloaded_only) searchParams.set("downloaded_only", "true");
    const qs = searchParams.toString();
    return apiFetch<ModelListResponse>(`/models${qs ? `?${qs}` : ""}`);
  },

  recommended: (workload?: string) => {
    const qs = workload ? `?workload=${encodeURIComponent(workload)}` : "";
    return apiFetch<RecommendedModelsAllResponse>(`/models/recommended${qs}`);
  },

  hardware: () =>
    apiFetch<HardwareInfo>("/models/hardware"),

  search: (params: { q?: string; capabilities?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params.q) searchParams.set("q", params.q);
    if (params.capabilities) searchParams.set("capabilities", params.capabilities);
    if (params.limit) searchParams.set("limit", String(params.limit));
    return apiFetch<{ models: ModelSearchResult[]; total_count: number }>(
      `/models/search?${searchParams.toString()}`,
    );
  },

  compare: (model_ids: string[]) =>
    apiFetch<ModelComparison>("/models/compare", {
      method: "POST",
      body: { model_ids },
    }),

  autocomplete: (q: string) =>
    apiFetch<{ suggestions: string[] }>(
      `/models/autocomplete?q=${encodeURIComponent(q)}`,
    ),

  detail: (modelId: string) =>
    apiFetch<ModelDetail>(`/models/${modelId}`),

  inferenceConfig: (modelId: string) =>
    apiFetch<{ model_id: string; context_length?: number; temperature: number; top_p: number; top_k: number; repeat_penalty: number; seed: number; num_predict: number; num_ctx?: number; image_resolution?: number }>(
      `/models/${modelId}/inference-config`,
    ),

  refresh: () =>
    apiFetch<RefreshCatalogResponse>("/models/refresh", { method: "POST" }),

  families: (): Promise<ModelFamiliesResponse> =>
    apiFetch<ModelFamiliesResponse>("/models/families"),

  familyVariants: (family: string): Promise<FamilyVariantsResponse> =>
    apiFetch<FamilyVariantsResponse>(`/models/families/${encodeURIComponent(family)}/variants`),
};
