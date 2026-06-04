import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { SyncRun, WorkspaceIntelligence } from "@/types/api";

export const syncService = {
  async triggerSync(): Promise<SyncRun> {
    const response = await apiClient.post<SyncRun>(API_ENDPOINTS.SYNC_TRIGGER, {});
    return response.data;
  },

  async getStatus(): Promise<any> {
    const response = await apiClient.get(API_ENDPOINTS.SYNC_STATUS);
    return response.data;
  },

  async getLatestRun(): Promise<SyncRun | null> {
    const response = await apiClient.get<SyncRun | null>(API_ENDPOINTS.SYNC_RUN_LATEST);
    return response.data || null;
  },

  async getRun(runId: string): Promise<SyncRun> {
    const response = await apiClient.get<SyncRun>(API_ENDPOINTS.SYNC_RUN.replace("{id}", runId));
    return response.data;
  },

  async getIntelligence(): Promise<WorkspaceIntelligence> {
    const response = await apiClient.get<WorkspaceIntelligence>("/workspace/intelligence");
    return response.data;
  },

  async getConfig(): Promise<any> {
    const response = await apiClient.get(API_ENDPOINTS.SYNC_CONFIG);
    return response.data;
  },

  async addIncludePath(path: string): Promise<any> {
    const response = await apiClient.post(API_ENDPOINTS.SYNC_CONFIG_INCLUDE, { path });
    return response.data;
  },

  async addExcludePath(path: string): Promise<any> {
    const response = await apiClient.post(API_ENDPOINTS.SYNC_CONFIG_EXCLUDE, { path });
    return response.data;
  },

  async removeIncludePath(path: string): Promise<any> {
    const response = await apiClient.post(`${API_ENDPOINTS.SYNC_CONFIG_INCLUDE}/remove`, { path });
    return response.data;
  },

  async removeExcludePath(path: string): Promise<any> {
    const response = await apiClient.post(`${API_ENDPOINTS.SYNC_CONFIG_EXCLUDE}/remove`, { path });
    return response.data;
  },
};
