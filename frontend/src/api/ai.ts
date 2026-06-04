import { api } from "./client";
import type { ContextItem } from "@/types/cortex";


export type GraphNode = {
  id: string;
  agent_name: string;
  depends_on: string[];
  status: "pending" | "running" | "completed" | "failed";
  execution_time: number;
  confidence: number;
  reasoning_summary: string;
  verified?: boolean | null;
  issues?: string[];
};

export type VerificationResults = {
  verified: boolean;
  issues: string[];
  report: string;
};

export type AskResponse = {
  query: string;
  response: string;
  user_id: number | null;
  execution_id: string | null;
  routing_info?: {
    model_used: string;
    provider: string;
    response_time: number;
    selection_reason: string;
    fallback_used?: boolean;
    fallback_reason?: string | null;
    classified_task?: string;
    agent_selected?: string;
    agent_confidence?: number;
    agent_execution_time?: number;
    agent_reason?: string;
    execution_order?: string[];
    collaboration_graph?: GraphNode[];
    verification_results?: VerificationResults | null;
  } | null;
};

export type ChatTurn = {
  role: "user" | "assistant";
  content: string;
};

export type HistoryResponseItem = {
  query: string;
  response: string;
};

export type ModelConfig = {
  llm_model: string;
  embedding_model: string;
  vector_db: string;
  inference_engine: string;
  code_parsing: string;
  api_key?: string;
  api_base_url?: string;
};

export type InstalledModel = {
  name: string;
  size: number;
  family: string;
  parameter_size: string;
  quantization_level: string;
};

export type UserSettings = {
  api_base_url: string | null;
  api_key_masked: string | null;
  llm_model?: string | null;
  embedding_model?: string | null;
  vector_db?: string | null;
  inference_engine?: string | null;
  code_parsing?: string | null;
  selected_model?: string | null;
};

export type WorkspaceIntelligenceEntryPoint = {
  path: string;
  role: string;
};

export type WorkspaceActivityFeedItem = {
  title: string;
  detail: string;
  tone: "success" | "info" | "warning" | "insight";
  count?: number | null;
};

export type WorkspaceGraph = {
  nodes: string[];
  edges: { source: string; target: string; relation: string }[];
};

export type WorkspaceRepositoryModel = {
  modules: string[];
  files: string[];
  classes: string[];
  functions: string[];
  apis: string[];
  configurations: string[];
  dependencies: string[];
  entry_points: string[];
  documentation: string[];
  relationships: { source: string; target: string; relation: string }[];
};

export type WorkspaceQueryClass = {
  name: string;
  retrieval: string;
  use_case: string;
};

export type WorkspaceMemorySummary = {
  patterns: string[];
  decisions: string[];
  known_bugs: string[];
  design_rationale: string[];
};

export type WorkspaceSystemAccess = {
  default_mode: string;
  modes: { name: string; description: string }[];
  read_permissions: string[];
  modify_permissions: string[];
  ignored_paths: string[];
  read_scope: string[];
  discovery_policy: string;
  autonomous_discovery: string[];
  approval_rules: string[];
  proactive_examples: string[];
};

export type WorkspaceIntelligenceResponse = {
  project_name: string;
  purpose: string;
  architecture: string[];
  repositories: string[];
  concepts: string[];
  repository_model: WorkspaceRepositoryModel;
  system_access: WorkspaceSystemAccess;
  dependency_graph: WorkspaceGraph;
  module_graph: WorkspaceGraph;
  knowledge_graph: WorkspaceGraph;
  query_classes: WorkspaceQueryClass[];
  memory_summary: WorkspaceMemorySummary;
  dependencies: string[];
  frameworks: string[];
  entrypoints: WorkspaceIntelligenceEntryPoint[];
  apis: string[];
  execution_flow: string[];
  config: string[];
  build_process: string[];
  key_files: string[];
  warnings: string[];
  activity_feed: WorkspaceActivityFeedItem[];
  evidence: { path: string; snippet: string }[];
};

export async function askQuestion(
  query: string,
  useAuthenticatedChat = false,
  history?: ChatTurn[],
  modelConfig?: ModelConfig,
  contextItems?: ContextItem[]
): Promise<AskResponse> {
  const url = useAuthenticatedChat ? "/ai/chat" : "/ai/ask";
  const res = await api.post(url, {
    query,
    history,
    ...modelConfig,
    // Map camelCase fields to snake_case for backend
    context_items: contextItems?.map((c) => ({
      id: c.id,
      kind: c.kind,
      title: c.title,
      detail: c.detail,
      path: c.path,
      url: c.url,
      content_preview: c.contentPreview,
    })),
  });
  return res.data;
}

export async function getChatHistory(limit = 50): Promise<HistoryResponseItem[]> {
  const res = await api.get("/ai/history", { params: { limit } });
  return res.data;
}

export async function getInstalledModels(): Promise<InstalledModel[]> {
  const res = await api.get("/models/installed");
  return res.data;
}

export async function checkModelInstalled(modelName: string): Promise<boolean> {
  const res = await api.get(`/models/check/${encodeURIComponent(modelName)}`);
  return res.data.installed;
}

export async function deleteModel(modelName: string): Promise<void> {
  await api.delete(`/models/${encodeURIComponent(modelName)}`);
}

export async function getUserSettings(): Promise<UserSettings> {
  const res = await api.get("/users/me/settings");
  return res.data;
}

export async function getWorkspaceIntelligence(): Promise<WorkspaceIntelligenceResponse> {
  const res = await api.get("/workspace/intelligence");
  return res.data;
}

export async function updateUserSettings(settings: {
  api_base_url?: string;
  api_key?: string;
  llm_model?: string;
  embedding_model?: string;
  vector_db?: string;
  inference_engine?: string;
  code_parsing?: string;
  selected_model?: string;
}): Promise<UserSettings> {
  const res = await api.put("/users/me/settings", settings);
  return res.data;
}

export type ModelDownloadJob = {
  id: string;
  model: string;
  status: "queued" | "running" | "paused" | "completed" | "failed" | "cancelled";
  percent: number;
  completed: number;
  total: number;
  message: string;
  error?: string | null;
  created_at: string;
  updated_at: string;
};

export async function startModelDownload(modelName: string): Promise<ModelDownloadJob> {
  const res = await api.post("/models/pull", { model: modelName });
  return res.data;
}

export async function listModelDownloads(): Promise<ModelDownloadJob[]> {
  const res = await api.get("/models/downloads");
  return res.data;
}

export async function getModelDownload(jobId: string): Promise<ModelDownloadJob> {
  const res = await api.get(`/models/downloads/${encodeURIComponent(jobId)}`);
  return res.data;
}

export async function cancelModelDownload(jobId: string): Promise<ModelDownloadJob> {
  const res = await api.post(`/models/downloads/${encodeURIComponent(jobId)}/cancel`);
  return res.data;
}

export async function resumeModelDownload(jobId: string): Promise<ModelDownloadJob> {
  const res = await api.post(`/models/downloads/${encodeURIComponent(jobId)}/resume`);
  return res.data;
}

export type RegisteredModel = {
  id?: number;
  name: string;
  display_name?: string;
  provider: string;
  context_length?: number | null;
  parameters?: string | null;
  quantization?: string | null;
  vram_estimate?: string | null;
  status: string;
  is_local: boolean;
  tags?: string[];
  pull_command?: string;
  performance_tier?: string;
  vram_requirement_gb?: number;
  best_use_case?: string;
  default_for_provider?: boolean;
  source?: string;
};

export type Provider = {
  id?: number;
  name: string;
  base_url?: string | null;
  is_enabled: boolean;
  is_custom: boolean;
  has_key: boolean;
  default_model_name?: string | null;
};

export async function getAllModels(): Promise<RegisteredModel[]> {
  const res = await api.get("/models");
  return res.data;
}

export async function getProviders(): Promise<Provider[]> {
  const res = await api.get("/models/providers");
  return res.data;
}

export async function validateProvider(
  name: string,
  base_url: string,
  api_key: string
): Promise<ProviderModelsResponse> {
  const res = await api.post("/models/providers/validate", { name, base_url, api_key });
  return res.data;
}

export async function createProvider(provider: {
  name: string;
  base_url?: string;
  api_key?: string;
  default_model_name?: string;
  is_enabled: boolean;
  is_custom: boolean;
}): Promise<unknown> {
  const res = await api.post("/models/providers", provider);
  return res.data;
}

export async function updateProvider(
  name: string,
  provider: {
    name: string;
    base_url?: string;
    api_key?: string;
    default_model_name?: string;
    is_enabled: boolean;
    is_custom: boolean;
  }
): Promise<unknown> {
  const res = await api.put(`/models/providers/${encodeURIComponent(name)}`, provider);
  return res.data;
}

export async function deleteProvider(name: string): Promise<unknown> {
  const res = await api.delete(`/models/providers/${encodeURIComponent(name)}`);
  return res.data;
}

export async function selectModel(model_name: string, session_id?: string): Promise<unknown> {
  const res = await api.post("/models/select", { model_name, session_id });
  return res.data;
}

export interface RoutingProfile {
  name: string;
  is_active: boolean;
}

export interface TaskRoute {
  task_type: string;
  primary_model: string;
  fallback_model: string;
}

export interface RoutingRoutesResponse {
  profile_name: string;
  routes: TaskRoute[];
}

export async function getRoutingProfiles(): Promise<RoutingProfile[]> {
  const res = await api.get("/models/routing/profiles");
  return res.data;
}

export async function selectRoutingProfile(name: string): Promise<unknown> {
  const res = await api.post("/models/routing/profiles/select", { name });
  return res.data;
}

export async function getRoutingRoutes(): Promise<RoutingRoutesResponse> {
  const res = await api.get("/models/routing/routes");
  return res.data;
}

export async function updateRoutingRoutes(routes: TaskRoute[]): Promise<unknown> {
  const res = await api.post("/models/routing/routes", { routes });
  return res.data;
}

export interface MarketplaceModel {
  name: string;
  display_name: string;
  size: string;
  context_length: number;
  vram_requirement_gb: number;
  best_use_case: string;
  tags: string[];
  is_installed: boolean;
  download_status: "installed" | "available";
  pull_command?: string;
  performance_tier?: string;
  capabilities?: string[];
  vram_estimate?: string;
  source?: string;
}

export interface HardwareInfo {
  os: string;
  cpu: string;
  ram: {
    total_gb: number;
    available_gb: number;
    usage_percent: number;
  };
  gpu: {
    detected: boolean;
    name: string;
    total_vram_gb: number;
    free_vram_gb: number;
    utilization: number;
  };
}

export interface MetricsSummary {
  avg_response_time_ms: number;
  avg_tokens_per_second: number;
  cache_hit_rate_percent: number;
  gpu_usage_percent: number;
  vram_usage: {
    total_gb: number;
    used_gb: number;
    usage_percent: number;
  };
  memory_usage: {
    total_gb: number;
    used_gb: number;
    usage_percent: number;
  };
  total_requests: number;
  most_used_models: {
    model_name: string;
    provider_name: string;
    total_requests: number;
  }[];
}

export interface ModelHealth {
  model_name: string;
  provider_name: string;
  total_requests: number;
  success_rate: number;
  failure_rate: number;
  avg_latency_ms: number;
  last_used_at: string | null;
  status: "healthy" | "unstable" | "failing" | "inactive";
}

export interface TaskDistributionItem {
  task_key: string;
  task_type: string;
  count: number;
  avg_latency_ms: number;
  success_rate_percent: number;
}

export interface RoutingAnalytics {
  routing_mode: {
    auto: number;
    manual: number;
    total: number;
  };
  task_distribution: TaskDistributionItem[];
  profile_distribution: {
    profile_name: string;
    count: number;
  }[];
}

export async function getMarketplace(query?: string): Promise<MarketplaceModel[]> {
  const res = await api.get("/models/marketplace", { params: query ? { query } : undefined });
  return res.data;
}

export async function getHardwareInfo(): Promise<HardwareInfo> {
  const res = await api.get("/models/hardware");
  return res.data;
}

export async function getMetricsSummary(): Promise<MetricsSummary> {
  const res = await api.get("/models/metrics/summary");
  return res.data;
}

export async function getModelHealth(): Promise<ModelHealth[]> {
  const res = await api.get("/models/metrics/health");
  return res.data;
}

export async function getRoutingAnalytics(): Promise<RoutingAnalytics> {
  const res = await api.get("/models/metrics/analytics");
  return res.data;
}

export interface ProviderModelsResponse {
  provider_name?: string;
  default_model_name?: string | null;
  default_model?: string | null;
  models: string[];
  valid: boolean;
  test_response?: string | null;
  error?: string | null;
}

export async function getProviderModels(providerName: string): Promise<ProviderModelsResponse> {
  const res = await api.get(`/models/providers/${encodeURIComponent(providerName)}/models`);
  return res.data;
}

export async function setProviderDefaultModel(providerName: string, defaultModelName: string): Promise<{
  message: string;
  provider_name: string;
  default_model_name: string | null;
}> {
  const res = await api.put(`/models/providers/${encodeURIComponent(providerName)}/default-model`, {
    default_model_name: defaultModelName,
  });
  return res.data;
}

// Vault Management API
export type VaultCategoryStat = {
  size_bytes: number;
  file_count: number;
};

export type VaultSettings = {
  active_path: string;
  is_paused: boolean;
  total_size_bytes: number;
  categories: Record<string, VaultCategoryStat>;
};

export async function getVaultSettings(): Promise<VaultSettings> {
  const res = await api.get("/vault/settings");
  return res.data;
}

export async function changeVaultPath(path: string): Promise<{ status: string; message: string; active_path: string }> {
  const res = await api.post("/vault/change-path", { path });
  return res.data;
}

export async function resetVault(): Promise<{ status: string; message: string }> {
  const res = await api.post("/vault/reset");
  return res.data;
}

export async function exportVault(): Promise<Blob> {
  const res = await api.get("/vault/export", { responseType: "blob" });
  return res.data;
}

export async function importVault(file: File): Promise<{ status: string; message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/vault/import", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return res.data;
}
