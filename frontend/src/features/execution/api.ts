/**
 * Execution API Client — v1.06 Cognition & Execution Core
 *
 * Covers: Tool execution, workflows, tool registry
 * Backend routes: /api/v1/execution/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface ToolExecution {
  id: number;
  user_id: number;
  tool_name: string;
  parameters: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
  error_type: string | null;
  verification_result: Record<string, unknown> | null;
  retry_count: number;
  parent_execution_id: number | null;
  workflow_id: number | null;
}

export interface ToolInfo {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  requires_confirmation: boolean;
  category: string;
}

export interface ExecutionStats {
  total: number;
  successful: number;
  failed: number;
  blocked: number;
  timeout: number;
  success_rate: number;
  average_duration_ms: number;
  tool_breakdown: Record<string, number>;
}

export interface Workflow {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  steps: WorkflowStep[];
  status: string;
  current_step: number;
  created_at: string;
  updated_at: string | null;
  last_run: string | null;
  last_run_status: string | null;
  run_count: number;
  total_duration_ms: number | null;
  error_message: string | null;
}

export interface WorkflowStep {
  tool: string;
  params?: Record<string, unknown>;
  status?: string;
  result?: Record<string, unknown>;
  depends_on?: number[];
  condition?: Record<string, unknown>;
  max_retries?: number;
  on_failure?: string;
  error?: string;
}

// ── Tools ──────────────────────────────────────────────────────────────────

export const tools = {
  execute: (toolName: string, parameters?: Record<string, unknown>, options?: { autoVerify?: boolean; confirmed?: boolean }) => {
    const qs = new URLSearchParams();
    if (options?.autoVerify !== undefined) qs.set("auto_verify", String(options.autoVerify));
    if (options?.confirmed !== undefined) qs.set("confirmed", String(options.confirmed));
    const qsStr = qs.toString();
    return apiFetch<ToolExecution>(
      `/tools/execute${qsStr ? `?${qsStr}` : ""}`,
      { method: "POST", body: { tool_name: toolName, parameters: parameters || {} } },
    );
  },

  executeWithRetry: (toolName: string, parameters?: Record<string, unknown>, maxRetries: number = 3) =>
    apiFetch<ToolExecution>(
      `/tools/execute-with-retry?max_retries=${maxRetries}`,
      { method: "POST", body: { tool_name: toolName, parameters: parameters || {} } },
    ),

  list: (category?: string) =>
    apiFetch<ToolInfo[]>(`/tools/list${category ? `?category=${category}` : ""}`),

  getStats: () =>
    apiFetch<ExecutionStats>("/tools/stats"),

  getExecution: (executionId: number) =>
    apiFetch<ToolExecution>(`/tools/${executionId}`),
};

// ── Workflows ──────────────────────────────────────────────────────────────

export const workflows = {
  create: (name: string, steps: WorkflowStep[], description?: string) =>
    apiFetch<Workflow>("/workflows/create", {
      method: "POST",
      body: { name, steps, description: description || null },
    }),

  list: (params?: { status?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.limit) qs.set("limit", String(params.limit));
    return apiFetch<Workflow[]>(`/workflows/list?${qs}`);
  },

  get: (workflowId: number) =>
    apiFetch<Workflow>(`/workflows/${workflowId}`),

  run: (workflowId: number) =>
    apiFetch<Workflow>(`/workflows/${workflowId}/run`, { method: "POST" }),

  cancel: (workflowId: number) =>
    apiFetch<Workflow>(`/workflows/${workflowId}/cancel`, { method: "POST" }),

  duplicate: (workflowId: number, newName: string) =>
    apiFetch<Workflow>(
      `/workflows/${workflowId}/duplicate?new_name=${encodeURIComponent(newName)}`,
      { method: "POST" },
    ),
};
