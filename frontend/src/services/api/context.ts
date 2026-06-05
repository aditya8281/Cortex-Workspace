import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";

export const contextService = {
  async attachContext(data: { path?: string; content?: string; metadata?: any }): Promise<any> {
    const response = await apiClient.post(API_ENDPOINTS.CONTEXT_ATTACH, data);
    return response.data;
  },

  async listContext(): Promise<any[]> {
    const response = await apiClient.get(API_ENDPOINTS.CONTEXT_LIST);
    const data = response.data as any;
    return data?.results ?? data ?? [];
  },
};
