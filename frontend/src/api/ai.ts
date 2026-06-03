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
