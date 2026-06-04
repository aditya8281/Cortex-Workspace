import { apiClient } from "./client";
import { API_ENDPOINTS } from "@/constants/endpoints";
import type { User, TokenResponse, LoginRequest, RegisterRequest } from "@/types/api";

export const authService = {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>(API_ENDPOINTS.AUTH_LOGIN, credentials);
    if (response.data.access_token) {
      localStorage.setItem("auth_token", response.data.access_token);
      if (response.data.user) {
        localStorage.setItem("user", JSON.stringify(response.data.user));
      }
    }
    return response.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>(API_ENDPOINTS.AUTH_REGISTER, data);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH_ME);
    return response.data;
  },

  logout(): void {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
  },

  getToken(): string | null {
    return typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  },

  getCurrentUserFromStorage(): User | null {
    if (typeof window === "undefined") return null;
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  },
};
