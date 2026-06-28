import { apiFetch } from "@/shared/api/client";

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  active_connections: number;
  requests_today: number;
  avg_response_ms: number;
  uptime_seconds: number;
}

export interface SystemLog {
  timestamp: string;
  level: string;
  message: string;
  module: string;
}

export interface LLMHealth {
  ollama: "healthy" | "degraded" | "down";
  active_model: string | null;
  installed_models: string[];
  requests_per_minute: number;
  avg_latency_ms: number;
}

export interface LLMMetrics {
  total_requests: number;
  total_tokens: number;
  avg_tokens_per_request: number;
  error_rate: number;
}

export const systemApi = {
  getMetrics: () => apiFetch<SystemMetrics>("/system/metrics"),
  getLogs: (limit = 50) => apiFetch<{ logs: SystemLog[] }>(`/system/logs?limit=${limit}`),
  getLLMHealth: () => apiFetch<LLMHealth>("/models/health"),
  getLLMMetrics: () => apiFetch<LLMMetrics>("/models/metrics"),
};
