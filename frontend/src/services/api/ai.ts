import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { ChatRequest, ChatResponse, ChatMessage } from "@/types/api";

export const aiService = {
  async ask(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(API_ENDPOINTS.AI_ASK, request);
    return response.data;
  },

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(API_ENDPOINTS.AI_CHAT, request);
    return response.data;
  },

  async getHistory(): Promise<ChatMessage[]> {
    const response = await apiClient.get<ChatMessage[]>(API_ENDPOINTS.AI_HISTORY);
    return response.data || [];
  },

  async getExecution(executionId: string) {
    const response = await apiClient.get(`${API_ENDPOINTS.EXECUTION_DETAIL.replace("{id}", executionId)}`);
    return response.data;
  },

  async replayExecution(executionId: string) {
    const response = await apiClient.get(`${API_ENDPOINTS.EXECUTION_REPLAY.replace("{id}", executionId)}`);
    return response.data;
  },
};
