import { apiFetch } from "@/shared/api/client";

export interface HealthStatus {
  status: "healthy" | "degraded" | "down";
  database: "connected" | "disconnected";
  redis: "connected" | "disconnected";
  uptime_seconds: number;
}

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  active_connections: number;
  requests_today: number;
  avg_response_ms: number;
}

export interface LLMHealth {
  ollama: "healthy" | "degraded" | "down";
  active_model: string | null;
  requests_per_minute: number;
  avg_latency_ms: number;
}

export interface ActivityItem {
  id: string;
  type: "conversation" | "agent" | "system" | "error";
  title: string;
  description: string;
  timestamp: string;
}

export const dashboardApi = {
  getHealth: () => apiFetch<HealthStatus>("/system/health/live"),
  getDeepHealth: () => apiFetch<HealthStatus>("/system/health/deep"),
  getMetrics: () => apiFetch<SystemMetrics>("/system/metrics"),
  getLLMHealth: () => apiFetch<LLMHealth>("/models/health"),
  getRecentActivity: () =>
    apiFetch<{ items: ActivityItem[] }>("/conversations?limit=5").catch(() => ({
      items: [] as ActivityItem[],
    })),
};
