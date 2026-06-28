"use client";

import { apiFetch } from "@/shared/api/client";

export interface SystemMetrics {
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  gpu_name: string | null;
  gpu_type: string | null;
  gpu_percent: number | null;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  processes: ProcessInfo[];
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu: number;
  memory: number;
  status: string;
}

export interface LLMHealthResponse {
  status: string;
  latency_ms: number;
  error: string | null;
}

export interface LLMMetricsResponse {
  total_requests: number;
  total_tokens: number;
  avg_latency: number;
}

export interface ActivityItem {
  id: string;
  type: "conversation" | "agent" | "system" | "error";
  title: string;
  description: string;
  timestamp: string;
}

export const dashboardApi = {
  getMetrics: () => apiFetch<SystemMetrics>("/system/metrics"),
  getLLMHealth: () => apiFetch<LLMHealthResponse>("/models/health"),
  getLLMMetrics: () => apiFetch<LLMMetricsResponse>("/models/metrics"),
  getRecentActivity: () =>
    apiFetch<{ items: ActivityItem[] }>("/conversations?limit=5").catch(() => ({
      items: [] as ActivityItem[],
    })),
};
