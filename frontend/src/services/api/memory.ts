import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { MemoryItem, HierarchicalMemory } from "@/types/api";

export const memoryService = {
  async searchMemory(query: string): Promise<any[]> {
    const response = await apiClient.get<any>(API_ENDPOINTS.MEMORY_SEARCH, {
      params: { q: query },
    });
    return response.data?.results || [];
  },

  async getKnowledge(): Promise<any> {
    const response = await apiClient.get(API_ENDPOINTS.MEMORY_KNOWLEDGE);
    return response.data;
  },

  async getVaultSettings(): Promise<any> {
    const response = await apiClient.get(API_ENDPOINTS.VAULT_SETTINGS);
    return response.data;
  },

  async changeVaultPath(path: string): Promise<any> {
    const response = await apiClient.post(API_ENDPOINTS.VAULT_SETTINGS.replace("settings", "change-path"), { path });
    return response.data;
  },

  async exportVault(): Promise<any> {
    const response = await apiClient.get(API_ENDPOINTS.VAULT_EXPORT);
    return response.data;
  },

  async importVault(data: FormData): Promise<{ imported_items: number }> {
    const response = await apiClient.post(API_ENDPOINTS.VAULT_IMPORT, data);
    return response.data;
  },

  async searchHierarchical(query: string): Promise<any[]> {
    const response = await apiClient.get<any>(API_ENDPOINTS.HIERARCHICAL_SEARCH, {
      params: { query },
    });
    return response.data?.results || [];
  },

  async expandGraph(nodeId: string): Promise<any> {
    const response = await apiClient.get(API_ENDPOINTS.HIERARCHICAL_EXPAND, {
      params: { node_id: nodeId },
    });
    return response.data;
  },
};
