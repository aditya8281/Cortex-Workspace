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
    agent_selected?: string;
    agent_confidence?: number;
    agent_execution_time?: number;
    agent_reason?: string;
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

export type ContextItemKind =
  | "file"
  | "folder"
  | "repo"
  | "memory"
  | "url"
  | "terminal"
  | "document"
  | "concept"
  | "activity";

export type ContextItem = {
  id: string;
  kind: ContextItemKind;
  title: string;
  detail?: string;
  // Optional fields for specific kinds
  path?: string;           // for file/folder
  url?: string;            // for url
  contentPreview?: string; // terminal paste or extracted snippet
  resolvedContent?: string; // populated by the backend ContextResolver
  selectedModel?: string;  // for repo context
};
