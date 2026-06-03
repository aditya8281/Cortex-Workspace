import { api } from "./client";

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
  modelConfig?: ModelConfig
): Promise<AskResponse> {
  const url = useAuthenticatedChat ? "/ai/chat" : "/ai/ask";
  const res = await api.post(url, { query, history, ...modelConfig });
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

export async function updateUserSettings(settings: { api_base_url?: string; api_key?: string }): Promise<UserSettings> {
  const res = await api.put("/users/me/settings", settings);
  return res.data;
}

export async function pullModel(
  modelName: string,
  onProgress: (progress: { status: string; percent: number; completed: number; total: number }) => void
): Promise<void> {
  const token = localStorage.getItem("cortex_token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const baseUrl = (api.defaults.baseURL || import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

  const response = await fetch(`${baseUrl}/models/pull`, {
    method: "POST",
    headers,
    body: JSON.stringify({ model: modelName }),
  });

  if (!response.ok) {
    throw new Error(`Failed to start pulling model: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body reader available");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const dataStr = line.slice(6).trim();
          const parsed = JSON.parse(dataStr);
          onProgress(parsed);
        } catch (e) {
          console.error("Failed to parse SSE line", line, e);
        }
      }
    }
  }
}

export type RegisteredModel = {
  id?: number;
  name: string;
  provider: string;
  context_length?: number | null;
  parameters?: string | null;
  quantization?: string | null;
  vram_estimate?: string | null;
  status: string;
  is_local: boolean;
};

export type Provider = {
  id?: number;
  name: string;
  base_url?: string | null;
  is_enabled: boolean;
  is_custom: boolean;
  has_key: boolean;
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
): Promise<{ valid: boolean; models: string[]; test_response?: string; error?: string }> {
  const res = await api.post("/models/providers/validate", { name, base_url, api_key });
  return res.data;
}

export async function createProvider(provider: {
  name: string;
  base_url?: string;
  api_key?: string;
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

export async function selectModel(model_name: string): Promise<unknown> {
  const res = await api.post("/models/select", { model_name });
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

