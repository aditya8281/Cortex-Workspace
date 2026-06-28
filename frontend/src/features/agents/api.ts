import { apiFetch } from "@/shared/api/client";

export interface Agent {
  id: number;
  name: string;
  description: string | null;
  system_prompt: string;
  model_id: string;
  tools: string[] | null;
  is_active: boolean;
  run_count: number;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: number;
  agent_id: number;
  agent_name?: string;
  input: string;
  output: string | null;
  status: "pending" | "running" | "completed" | "failed";
  token_usage: number;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AgentStep {
  id: number;
  run_id: number;
  step_number: number;
  tool_name: string | null;
  tool_input: string | null;
  tool_output: string | null;
  reasoning: string | null;
  status: string;
  created_at: string;
}

export const agentsApi = {
  list: () => apiFetch<{ agents: Agent[] }>("/agents"),

  get: (id: number) => apiFetch<Agent>(`/agents/${id}`),

  create: (data: { name: string; description?: string; system_prompt: string; model_id?: string; tools?: string[] }) =>
    apiFetch<Agent>("/agents", {
      method: "POST",
      body: data,
    }),

  update: (id: number, data: Partial<{ name: string; description: string; system_prompt: string; model_id: string; is_active: boolean; tools: string[] }>) =>
    apiFetch<Agent>(`/agents/${id}`, {
      method: "PATCH",
      body: data,
    }),

  delete: (id: number) =>
    apiFetch<{ status: string }>(`/agents/${id}`, { method: "DELETE" }),

  listRuns: (agentId?: number, status?: string, limit = 20) => {
    const params = new URLSearchParams();
    if (agentId) params.set("agent_id", String(agentId));
    if (status) params.set("status", status);
    params.set("limit", String(limit));
    return apiFetch<{ runs: AgentRun[] }>(`/agents/runs?${params}`);
  },

  getRun: (runId: number) =>
    apiFetch<{ run: AgentRun; steps: AgentStep[] }>(`/agents/runs/${runId}`),

  startRun: (agentId: number, input: string) =>
    apiFetch<{ status: string; run_id: number }>("/agents/runs", {
      method: "POST",
      body: { agent_id: agentId, input },
    }),
};
