import { api } from "./client";

export type AskResponse = {
  query: string;
  response: string;
  user_id: number | null;
  execution_id: string | null;
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

  const response = await fetch("http://localhost:8000/api/v1/models/pull", {
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
