import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { User, HealthStatus, APILogEntry, SystemMetrics } from "@/types/api";

export const healthService = {
  async checkLive(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>(API_ENDPOINTS.HEALTH_LIVE);
    return response.data;
  },

  async checkReady(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>(API_ENDPOINTS.HEALTH_READY);
    return response.data;
  },

  async checkDeep(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>(API_ENDPOINTS.HEALTH_DEEP);
    return response.data;
  },
};

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  role?: 'user' | 'admin';
}

export const adminService = {
  async listUsers(): Promise<User[]> {
    const response = await apiClient.get<User[]>(API_ENDPOINTS.ADMIN_USERS);
    return response.data || [];
  },

  async getUser(userId: string | number): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.ADMIN_USER_DETAIL.replace("{id}", String(userId)));
    return response.data || ({} as User);
  },

  async updateUser(userId: string | number, data: UserUpdateRequest): Promise<User> {
    const response = await apiClient.put(API_ENDPOINTS.ADMIN_USER_DETAIL.replace("{id}", String(userId)), data);
    return response.data;
  },

  async deleteUser(userId: string | number): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.ADMIN_USER_DETAIL.replace("{id}", String(userId)));
  },

  async getExecutionLogs(limit: number = 50): Promise<APILogEntry[]> {
    const response = await apiClient.get<APILogEntry[]>(API_ENDPOINTS.EXECUTION_LIST, {
      params: { limit },
    });
    return response.data || [];
  },

  async getMetrics(): Promise<SystemMetrics> {
    try {
      const response = await apiClient.get<any>("/models/metrics/summary");
      return response.data || { availability: 0, avg_latency_ms: 0, error_rate: 0, cpu_usage: 0, memory_usage_mb: 0 };
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
      return { availability: 0, avg_latency_ms: 0, error_rate: 0, cpu_usage: 0, memory_usage_mb: 0 };
    }
  },

  async getModelHealth(): Promise<any[]> {
    const response = await apiClient.get<any[]>("/models/metrics/health");
    return response.data || [];
  },

  async listServices(): Promise<any[]> {
    const response = await apiClient.get<any[]>("/health/services");
    return response.data || [];
  },

  async restartService(name: string): Promise<any> {
    const response = await apiClient.post(`/health/services/${name}/restart`);
    return response.data;
  },
};
