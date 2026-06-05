// User & Auth
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "user" | "admin";
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

// API Response Wrapper
export interface APIResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

export interface CortexModel {
  id: string;
  name: string;
  type: "local" | "cloud" | "custom" | string;
  provider_id?: string;
  context_length?: number;
  capabilities?: string[];
  metadata?: Record<string, any>;
  parameters?: string;
  api_endpoint?: string;
  status?: string;
  provider_name?: string;
  is_custom?: boolean;
}

export interface CortexProvider {
  id: string;
  name: string;
  api_base_url?: string;
  status: "active" | "inactive";
  models?: CortexModel[];
}

export interface CortexRoutingProfile {
  id: string;
  name: string;
  is_active: boolean;
  description?: string;
}

export interface CortexTaskRoute {
  task_type: string;
  primary_model: string;
  fallback_model: string;
}

// Chat
export interface ChatMessage {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  execution_id?: string;
}

export interface ChatRequest {
  query: string;
  history?: ChatMessage[];
  llm_model?: string;
  embedding_model?: string;
  vector_db?: string;
  inference_engine?: string;
  code_parsing?: boolean;
  context_items?: ContextItem[];
}

export interface ContextItem {
  id?: string;
  type: string;
  content: string;
  [key: string]: string | undefined;
}

export interface ChatResponse {
  query: string;
  response: string;
  execution_id?: string;
  routing_info?: Record<string, any>;
  user_id?: number;
}

// Sync
export interface SyncRun {
  id: number;
  user_id?: number;
  status: "running" | "complete" | "error";
  progress_message: string;
  start_time?: string;
  end_time?: string;
  file_count?: number;
}

export interface WorkspaceIntelligence {
  total_files: number;
  indexed_files: number;
  status: string;
  last_sync?: string;
  next_sync?: string;
}

// Health
export interface HealthStatus {
  status: "alive" | "ready" | "not_ready" | "healthy" | "degraded";
  database?: boolean;
  memory?: boolean;
  rag?: boolean;
  checks?: {
    database?: boolean;
    memory?: boolean;
    rag?: boolean;
  };
}

// Execution
export interface ExecutionResult {
  execution_id: string;
  status: string;
  summary?: string;
  tools_used?: string[];
  duration_ms?: number;
}

// Memory
export interface MemoryItem {
  id: string;
  key: string;
  value: string;
  category?: string;
  created_at?: string;
}

export interface HierarchicalMemory {
  id: string;
  parent_id?: string;
  name: string;
  type: string;
  content: string;
  level: number;
  path: string;
}

// Admin
export interface SystemMetrics {
  availability: number;
  avg_latency_ms: number;
  error_rate: number;
  cpu_usage: number;
  memory_usage_mb: number;
}

export interface APILogEntry {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "DEBUG";
  message: string;
  details?: Record<string, any>;
}

export type AuthState = "authenticated" | "unauthenticated" | "loading";
export type UserRole = "user" | "admin";
