import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { SyncRun, WorkspaceIntelligence } from "@/types/api";

export const syncService = {
  async triggerSync(signal?: AbortSignal): Promise<SyncRun> {
    const resp = await apiClient.postSafe<SyncRun>(API_ENDPOINTS.SYNC_TRIGGER, {}, { signal });
    return resp.data ?? ({} as SyncRun);
  },

  async getStatus(signal?: AbortSignal): Promise<any> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.SYNC_STATUS, { signal });
    return resp.data ?? null;
  },

  async getLatestRun(signal?: AbortSignal): Promise<SyncRun | null> {
    const resp = await apiClient.getSafe<SyncRun | null>(API_ENDPOINTS.SYNC_RUN_LATEST, { signal });
    return resp.data ?? null;
  },

  async getRun(runId: string, signal?: AbortSignal): Promise<SyncRun> {
    const resp = await apiClient.getSafe<SyncRun>(API_ENDPOINTS.SYNC_RUN.replace("{id}", runId), { signal });
    return resp.data ?? ({} as SyncRun);
  },

  async getIntelligence(signal?: AbortSignal): Promise<WorkspaceIntelligence> {
    const resp = await apiClient.getSafe<WorkspaceIntelligence>(API_ENDPOINTS.WORKSPACE_INTELLIGENCE, { signal });
    return resp.data ?? ({} as WorkspaceIntelligence);
  },

  async getConfig(): Promise<any> {
    const resp = await apiClient.getSafe(API_ENDPOINTS.SYNC_CONFIG);
    return resp.data ?? null;
  },

  async addIncludePath(path: string): Promise<any> {
    const resp = await apiClient.postSafe(API_ENDPOINTS.SYNC_CONFIG_INCLUDE, { path });
    return resp.data ?? null;
  },

  async addExcludePath(path: string): Promise<any> {
    const resp = await apiClient.postSafe(API_ENDPOINTS.SYNC_CONFIG_EXCLUDE, { path });
    return resp.data ?? null;
  },

  async removeIncludePath(path: string): Promise<any> {
    const resp = await apiClient.postSafe(`${API_ENDPOINTS.SYNC_CONFIG_INCLUDE}/remove`, { path });
    return resp.data ?? null;
  },

  async removeExcludePath(path: string): Promise<any> {
    const resp = await apiClient.postSafe(`${API_ENDPOINTS.SYNC_CONFIG_EXCLUDE}/remove`, { path });
    return resp.data ?? null;
  },
};
