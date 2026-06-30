/**
 * Context & Attention API Client — aligned with backend v1 awareness endpoints
 *
 * Covers: System Snapshots, Attention Sessions, Context Rules, State, Events
 * Backend routes: /api/v1/awareness/system/*, /attention/*, /context/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types (matching backend Pydantic schemas) ──────────────────────────────

export interface SystemSnapshot {
  id: number;
  user_id: number | null;
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  network_sent_bytes: number;
  network_recv_bytes: number;
  load_average_1m: number;
  load_average_5m: number;
  load_average_15m: number;
  process_count: number;
  uptime_seconds: number;
  created_at: string;
  meta: Record<string, unknown>;
}

export interface Anomaly {
  type: string;
  value: number;
  threshold: number;
}

export interface AttentionSession {
  id: number;
  user_id: number;
  session_type: string;
  task_description: string | null;
  focus_score: number;
  duration_minutes: number | null;
  started_at: string;
  ended_at: string | null;
  meta: Record<string, unknown>;
}

export interface AttentionStats {
  total_sessions: number;
  total_duration_minutes: number;
  average_focus: number;
  sessions_by_type: Record<string, number>;
}

export interface ContextRule {
  id: number;
  user_id: number;
  name: string;
  rule_type: string;
  description: string | null;
  enabled: boolean;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>;
  priority: number;
  hit_count: number;
  last_hit_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContextState {
  id: number;
  user_id: number;
  state_key: string;
  state_value: Record<string, unknown>;
  source: string;
  confidence: number;
  created_at: string;
  updated_at: string;
}

export interface ContextEvent {
  id: number;
  user_id: number;
  event_type: string;
  event_data: Record<string, unknown>;
  source: string;
  relevance_score: number;
  related_rule_id: number | null;
  created_at: string;
}

// ── System API ─────────────────────────────────────────────────────────────

export const systemApi = {
  takeSnapshot: () =>
    apiFetch<SystemSnapshot>("/system/snapshot", { method: "POST" }),

  getRecent: (limit = 20) =>
    apiFetch<{ snapshots: SystemSnapshot[]; total: number }>(
      `/system/recent?limit=${limit}`,
    ),

  getAnomalies: (params?: { threshold_cpu?: number; threshold_memory?: number; threshold_disk?: number }) => {
    const qs = new URLSearchParams();
    if (params?.threshold_cpu != null) qs.set("threshold_cpu", String(params.threshold_cpu));
    if (params?.threshold_memory != null) qs.set("threshold_memory", String(params.threshold_memory));
    if (params?.threshold_disk != null) qs.set("threshold_disk", String(params.threshold_disk));
    const query = qs.toString();
    return apiFetch<{ anomalies: Anomaly[] }>(
      `/system/anomalies${query ? `?${query}` : ""}`,
    );
  },
};

// ── Attention API ──────────────────────────────────────────────────────────

export const attentionApi = {
  startSession: (data: { session_type: string; task_description?: string }) =>
    apiFetch<AttentionSession>("/attention/session", {
      method: "POST",
      body: data,
    }),

  endSession: (id: number) =>
    apiFetch<AttentionSession>(`/attention/session/${id}/end`, {
      method: "POST",
    }),

  focusSession: (id: number, focus_score: number) =>
    apiFetch<AttentionSession>(`/attention/session/${id}/focus`, {
      method: "POST",
      body: { focus_score },
    }),

  getSessions: (limit = 20) =>
    apiFetch<{ sessions: AttentionSession[]; total: number }>(
      `/attention/sessions?limit=${limit}`,
    ),

  getStats: () => apiFetch<AttentionStats>("/attention/stats"),
};

// ── Context Rules API ─────────────────────────────────────────────────────

export const contextRulesApi = {
  create: (data: {
    name: string;
    rule_type: string;
    description?: string;
    conditions?: Record<string, unknown>;
    actions?: Record<string, unknown>;
    priority?: number;
  }) => apiFetch<ContextRule>("/context/rules", { method: "POST", body: data }),

  list: (rule_type?: string) => {
    const qs = rule_type ? `?rule_type=${encodeURIComponent(rule_type)}` : "";
    return apiFetch<ContextRule[]>(`/context/rules${qs}`);
  },

  update: (
    id: number,
    data: { name?: string; priority?: number; enabled?: boolean },
  ) => {
    const qs = new URLSearchParams();
    if (data.name != null) qs.set("name", data.name);
    if (data.priority != null) qs.set("priority", String(data.priority));
    if (data.enabled != null) qs.set("enabled", String(data.enabled));
    const query = qs.toString();
    return apiFetch<ContextRule>(
      `/context/rules/${id}${query ? `?${query}` : ""}`,
      { method: "PUT" },
    );
  },

  remove: (id: number) =>
    apiFetch<void>(`/context/rules/${id}`, { method: "DELETE" }),

  match: (context: Record<string, unknown>) =>
    apiFetch<{ matched_rules: ContextRule[] }>("/context/rules/match", {
      method: "POST",
      body: { context },
    }),
};

// ── Context State API ─────────────────────────────────────────────────────

export const contextStateApi = {
  get: (key: string) =>
    apiFetch<ContextState>(`/context/state/${encodeURIComponent(key)}`),

  upsert: (key: string, data: Record<string, unknown>) =>
    apiFetch<ContextState>(`/context/state/${encodeURIComponent(key)}`, {
      method: "PUT",
      body: data,
    }),

  list: () => apiFetch<ContextState[]>("/context/state"),
};

// ── Context Events API ────────────────────────────────────────────────────

export const contextEventsApi = {
  create: (data: {
    event_type: string;
    event_data?: Record<string, unknown>;
    source?: string;
    relevance_score?: number;
    related_rule_id?: number;
  }) => apiFetch<ContextEvent>("/context/events", { method: "POST", body: data }),

  list: (params?: { event_type?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.event_type) qs.set("event_type", params.event_type);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    const query = qs.toString();
    return apiFetch<ContextEvent[]>(`/context/events${query ? `?${query}` : ""}`);
  },
};
