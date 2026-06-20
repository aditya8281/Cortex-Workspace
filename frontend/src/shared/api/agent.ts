/**
 * Agent API client — CRUD, runs, steps, and feedback.
 */

import { api } from "./client";
import type { Agent, AgentListResponse, AgentRun, AgentStep, RunDetailResponse, RunListResponse } from "../types";

export const agentApi = {
  /** List all agents. */
  list: (): Promise<AgentListResponse> => {
    return api.get("/api/v1/agents");
  },

  /** Create a new agent. */
  create: (body: {
    name: string;
    description?: string;
    system_prompt: string;
    model_id?: string;
    tools?: string[];
  }): Promise<{ status: string; agent: Agent }> => {
    return api.post("/api/v1/agents", body);
  },

  /** Get a specific agent. */
  get: (agentId: number): Promise<{ agent: Agent }> => {
    return api.get(`/api/v1/agents/${agentId}`);
  },

  /** Update an agent. */
  update: (
    agentId: number,
    body: {
      name?: string;
      description?: string;
      system_prompt?: string;
      model_id?: string;
      is_active?: boolean;
    },
  ): Promise<{ status: string }> => {
    return api.put(`/api/v1/agents/${agentId}`, body);
  },

  /** Delete an agent. */
  delete: (agentId: number): Promise<{ status: string }> => {
    return api.delete(`/api/v1/agents/${agentId}`);
  },

  /** Run an agent (starts in background, returns run_id). */
  run: (body: {
    agent_id: number;
    input: string;
  }): Promise<{ status: string; run_id: number }> => {
    return api.post("/api/v1/agents/runs", body);
  },

  /** Get status of a background run. */
  getRunStatus: (runId: number): Promise<{ run_id: number; status: string }> => {
    return api.get(`/api/v1/agents/runs/${runId}/status`);
  },

  /** List runs. */
  listRuns: (params?: {
    agent_id?: number;
    status?: string;
    limit?: number;
  }): Promise<RunListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.agent_id) searchParams.set("agent_id", String(params.agent_id));
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return api.get(`/api/v1/agents/runs${qs ? `?${qs}` : ""}`);
  },

  /** Get a specific run with steps. */
  getRun: (runId: number): Promise<RunDetailResponse> => {
    return api.get(`/api/v1/agents/runs/${runId}`);
  },

  /** Get steps for a run. */
  getRunSteps: (runId: number): Promise<{ steps: AgentStep[] }> => {
    return api.get(`/api/v1/agents/runs/${runId}/steps`);
  },

  /** Add feedback for a run. */
  addFeedback: (
    runId: number,
    body: { rating: number; comment?: string },
  ): Promise<{ status: string; feedback: { id: number; rating: number } }> => {
    return api.post(`/api/v1/agents/runs/${runId}/feedback`, body);
  },
};
