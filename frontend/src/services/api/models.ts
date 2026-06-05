import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { CortexModel, CortexProvider, CortexRoutingProfile, CortexTaskRoute } from "@/types/api";

export interface CreateCustomModelRequest {
  name: string;
  model_type: string;
  [key: string]: string | number | boolean | undefined;
}

export interface UpdateProviderRequest {
  api_key?: string;
  api_base_url?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface MarketplaceModel {
  id: string;
  name: string;
  description?: string;
  [key: string]: string | undefined;
}

export interface HardwareInfo {
  cpu: string;
  memory: string;
  gpu?: string;
  [key: string]: string | undefined;
}

export interface DownloadProgress {
  job_id: string;
  status: string;
  progress: number;
  [key: string]: string | number | undefined;
}

export const modelsService = {
  // List
  async listAllModels(): Promise<CortexModel[]> {
    const resp = await apiClient.getSafe<CortexModel[]>(API_ENDPOINTS.MODELS_LIST);
    return Array.isArray(resp.data) ? resp.data : [];
  },

  async listByType(type: string): Promise<CortexModel[]> {
    const response = await apiClient.get<CortexModel[]>(`${API_ENDPOINTS.MODELS_BY_TYPE}/${type}`);
    return response.data || [];
  },

  async listInstalled(): Promise<CortexModel[]> {
    const response = await apiClient.get<CortexModel[]>(API_ENDPOINTS.MODELS_INSTALLED);
    return response.data || [];
  },

  // Selection
  async selectModel(modelName: string): Promise<{ selected_model: string }> {
    // Backend expects payload { model_name: string, session_id?: string }
    const response = await apiClient.post<{ selected_model: string }>(API_ENDPOINTS.MODELS_SELECT, { model_name: modelName });
    return response.data || { selected_model: modelName };
  },

  // Custom Models
  async listCustomModels(): Promise<CortexModel[]> {
    const response = await apiClient.get<CortexModel[]>(API_ENDPOINTS.MODELS_CUSTOM);
    return response.data || [];
  },

  async createCustomModel(data: CreateCustomModelRequest): Promise<CortexModel> {
    const response = await apiClient.post<CortexModel>(API_ENDPOINTS.MODELS_CUSTOM, data);
    return response.data;
  },

  async updateCustomModel(name: string, data: CreateCustomModelRequest): Promise<CortexModel> {
    const response = await apiClient.put<CortexModel>(
      API_ENDPOINTS.MODELS_CUSTOM_ITEM.replace("{name}", name),
      data
    );
    return response.data;
  },

  async deleteCustomModel(name: string): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.MODELS_CUSTOM_ITEM.replace("{name}", name));
  },

  // Providers
  async listProviders(): Promise<CortexProvider[]> {
    const resp = await apiClient.getSafe<CortexProvider[]>(API_ENDPOINTS.MODELS_PROVIDERS);
    return Array.isArray(resp.data) ? resp.data : [];
  },

  async addProvider(data: UpdateProviderRequest): Promise<CortexProvider> {
    const response = await apiClient.post<CortexProvider>(API_ENDPOINTS.MODELS_PROVIDERS, data);
    return response.data;
  },

  async updateProvider(name: string, data: UpdateProviderRequest): Promise<CortexProvider> {
    const response = await apiClient.put<CortexProvider>(
      `${API_ENDPOINTS.MODELS_PROVIDERS}/${name}`,
      data
    );
    return response.data;
  },

  async deleteProvider(name: string): Promise<void> {
    await apiClient.delete(`${API_ENDPOINTS.MODELS_PROVIDERS}/${name}`);
  },

  async validateProvider(data: UpdateProviderRequest): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await apiClient.post(API_ENDPOINTS.MODELS_PROVIDERS_VALIDATE, data);
    return response.data;
  },

  // Marketplace
  async getMarketplace(query?: string): Promise<MarketplaceModel[]> {
    const response = await apiClient.get<MarketplaceModel[]>(API_ENDPOINTS.MODELS_MARKETPLACE, {
      params: { query },
    });
    return response.data || [];
  },

  // Hardware
  async getHardwareInfo(): Promise<HardwareInfo> {
    const response = await apiClient.get<HardwareInfo>(API_ENDPOINTS.MODELS_HARDWARE);
    return response.data || {};
  },

  // Downloads
  async startDownload(modelName: string, signal?: AbortSignal): Promise<DownloadProgress> {
    const resp = await apiClient.postSafe<any>(API_ENDPOINTS.MODELS_PULL, { model: modelName }, { signal });
    if (resp.data) {
      return {
        job_id: resp.data.id || resp.data.job_id || "",
        status: resp.data.status || "",
        progress: resp.data.percent ?? resp.data.progress ?? 0,
        model: resp.data.model || "",
        message: resp.data.message || "",
        error: resp.data.error || null,
      };
    }
    return { job_id: "", status: "", progress: 0 };
  },

  async getDownloadProgress(jobId: string, signal?: AbortSignal): Promise<DownloadProgress> {
    const resp = await apiClient.getSafe<any>(API_ENDPOINTS.MODELS_DOWNLOAD_JOB.replace("{job_id}", jobId), { signal });
    if (resp.data) {
      return {
        job_id: resp.data.id || resp.data.job_id || jobId,
        status: resp.data.status || "",
        progress: resp.data.percent ?? resp.data.progress ?? 0,
        model: resp.data.model || "",
        message: resp.data.message || "",
        error: resp.data.error || null,
      };
    }
    return { job_id: jobId, status: "", progress: 0 };
  },

  async cancelDownload(jobId: string): Promise<{ cancelled: boolean }> {
    const response = await apiClient.post<{ cancelled: boolean }>(
      `${API_ENDPOINTS.MODELS_DOWNLOAD_JOB.replace("{job_id}", jobId)}/cancel`
    );
    return response.data || { cancelled: false };
  },
};

export const routingService = {
  async getProfiles(): Promise<CortexRoutingProfile[]> {
    const response = await apiClient.get<CortexRoutingProfile[]>(API_ENDPOINTS.ROUTING_PROFILES);
    return response.data || [];
  },

  async selectProfile(name: string): Promise<{ selected_profile: string }> {
    const response = await apiClient.post<{ selected_profile: string }>(API_ENDPOINTS.ROUTING_PROFILES_SELECT, { name });
    return response.data || { selected_profile: name };
  },

  async getRoutes(): Promise<CortexTaskRoute[]> {
    const response = await apiClient.get<CortexTaskRoute[]>(API_ENDPOINTS.ROUTING_ROUTES);
    return response.data || [];
  },

  async updateRoutes(routes: CortexTaskRoute[]): Promise<{ routes_updated: number }> {
    const response = await apiClient.post<{ routes_updated: number }>(API_ENDPOINTS.ROUTING_ROUTES, { routes });
    return response.data || { routes_updated: 0 };
  },

  async getAnalytics(): Promise<{ total_queries: number; success_rate: number; [key: string]: number | string | undefined }> {
    const response = await apiClient.get<{ total_queries: number; success_rate: number }>(API_ENDPOINTS.ROUTING_ANALYTICS);
    return response.data || { total_queries: 0, success_rate: 0 };
  },
};
