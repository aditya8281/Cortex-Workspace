export type ChatMessage = {
  id: string;
  sender: "user" | "assistant";
  text: string;
  executionId?: string | null;
  timestamp: string;
  routingInfo?: {
    model_used: string;
    provider: string;
    response_time: number;
    selection_reason: string;
    fallback_used?: boolean;
    fallback_reason?: string | null;
    classified_task?: string;
  } | null;
};

export type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  pinned?: boolean;
  archived?: boolean;
  selectedModel?: string;
};

export type AppUser = {
  id: number;
  email: string;
  full_name: string;
  role: string;
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

export type ContextItem = {
  id: string;
  kind: "file" | "repo" | "memory" | "document" | "concept" | "activity";
  title: string;
  detail?: string;
};
