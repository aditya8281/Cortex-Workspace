import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { MemoryItem, HierarchicalMemory } from "@/types/api";

export const memoryService = {
  async searchMemory(query: string, signal?: AbortSignal): Promise<any[]> {
    const resp = await apiClient.getSafe<any>(API_ENDPOINTS.MEMORY_SEARCH, {
      params: { q: query },
      signal,
    });
    return resp.data?.results || [];
  },

  async getKnowledge(): Promise<any> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.MEMORY_KNOWLEDGE);
    return resp.data ?? null;
  },

  async getProactiveNotifications(): Promise<any[]> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.INTELLIGENCE_PROACTIVE);
    return Array.isArray(resp.data) ? resp.data : [];
  },

  async getVaultSettings(): Promise<any> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.VAULT_SETTINGS);
    return resp.data ?? null;
  },

  async changeVaultPath(path: string): Promise<any> {
    const resp = await apiClient.postSafe(API_ENDPOINTS.VAULT_CHANGE_PATH, { path });
    return resp.data ?? null;
  },

  async exportVault(): Promise<any> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.VAULT_EXPORT);
    return resp.data ?? null;
  },

  async importVault(data: FormData): Promise<{ imported_items: number }> {
    const resp = await apiClient.postSafe(API_ENDPOINTS.VAULT_IMPORT, data);
    return resp.data ?? { imported_items: 0 };
  },

  async searchHierarchical(query: string): Promise<any[]> {
    const resp = await apiClient.getSafe<any>(API_ENDPOINTS.HIERARCHICAL_SEARCH, {
      params: { query },
    });
    return resp.data?.results || [];
  },

  async expandGraph(nodeId: string): Promise<any> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.HIERARCHICAL_EXPAND, {
      params: { node_id: nodeId },
    });
    return resp.data ?? null;
  },
};
