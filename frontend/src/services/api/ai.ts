import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { ChatRequest, ChatResponse, ChatMessage } from "@/types/api";

export const aiService = {
  async ask(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
    const resp = await apiClient.postSafe<ChatResponse>(API_ENDPOINTS.AI_ASK, request, { signal });
    return resp.data ?? ({} as ChatResponse);
  },

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const resp = await apiClient.postSafe<ChatResponse>(API_ENDPOINTS.AI_CHAT, request);
    return resp.data ?? ({} as ChatResponse);
  },

  async getHistory(): Promise<ChatMessage[]> {
    const resp = await apiClient.getSafe<ChatMessage[]>(API_ENDPOINTS.AI_HISTORY);
    return Array.isArray(resp.data) ? resp.data : [];
  },

  async getExecution(executionId: string, signal?: AbortSignal) {
    const resp = await apiClient.getSafe(API_ENDPOINTS.EXECUTION_DETAIL.replace("{id}", executionId), { signal });
    return resp.data ?? null;
  },

  async replayExecution(executionId: string) {
    const resp = await apiClient.getSafe(API_ENDPOINTS.EXECUTION_REPLAY.replace("{id}", executionId));
    return resp.data ?? null;
  },
};
