/**
 * System API Client — aligned with backend v1 system endpoints
 *
 * Backend routes: /api/v1/system/*, /api/v1/models/health, /api/v1/models/metrics
 */
import { apiFetch } from "@/shared/api/client";

// ── Types (matching backend Pydantic schemas) ──────────────────────────────

export interface SystemProcess {
  pid: number;
  name: string;
  cpu: number;
  memory: number;
  status: string;
}

// Backend: SystemMetricsResponse
export interface SystemMetrics {
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  gpu_name: string;
  gpu_type: string;
  gpu_percent: number | null;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  processes: SystemProcess[];
}

// Backend: LLMHealthResponse
export interface LLMHealth {
  status: string;
  latency_ms: number;
  error: string | null;
}

// Backend: LLMMetricsResponse
export interface LLMMetrics {
  total_requests: number;
  total_tokens: number;
  avg_latency: number;
}

// ── Endpoints ──────────────────────────────────────────────────────────────

export const systemApi = {
  getMetrics: () => apiFetch<SystemMetrics>("/system/metrics"),

  getLogs: (limit = 50) =>
    apiFetch<{ logs: Record<string, any>[]; total: number }>(
      `/system/logs?limit=${limit}`,
    ),

  getLLMHealth: () => apiFetch<LLMHealth>("/models/health"),

  getLLMMetrics: () => apiFetch<LLMMetrics>("/models/metrics"),
};
