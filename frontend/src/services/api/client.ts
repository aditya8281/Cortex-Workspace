import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Clear auth and redirect to login
          if (typeof window !== "undefined") {
            localStorage.removeItem("auth_token");
            localStorage.removeItem("user");
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );
  }

  public get<T = any>(url: string, config?: any) {
    return this.client.get<T>(url, config);
  }

  public post<T = any>(url: string, data?: any, config?: any) {
    return this.client.post<T>(url, data, config);
  }

  public put<T = any>(url: string, data?: any, config?: any) {
    return this.client.put<T>(url, data, config);
  }

  public delete<T = any>(url: string, config?: any) {
    return this.client.delete<T>(url, config);
  }

  public patch<T = any>(url: string, data?: any, config?: any) {
    return this.client.patch<T>(url, data, config);
  }

  // Safe helpers that never throw and return a normalized shape
  public async getSafe<T = any>(url: string, config?: any): Promise<{ ok: boolean; data: T | null; error?: any }> {
    const maxAttempts = config?.retries ?? 3;
    let attempt = 0;
    const baseDelay = 300;
    while (attempt < maxAttempts) {
      try {
        const resp = await this.client.get<T>(url, config);
        return { ok: true, data: resp.data ?? null };
      } catch (error: any) {
        // If request was aborted, return a specific shape without noisy logs
        if (error?.code === "ERR_CANCELED" || error?.name === "CanceledError") {
          return { ok: false, data: null, error: { aborted: true } };
        }

        const status = error?.response?.status;
        // Do not retry on client errors (4xx) except 429 Too Many Requests
        if (status && status >= 400 && status < 500 && status !== 429) {
          console.error("API GET client error (non-retriable):", url, status);
          return { ok: false, data: null, error };
        }

        attempt += 1;
        if (attempt >= maxAttempts) {
          console.error("API GET error (safe):", url, error);
          return { ok: false, data: null, error };
        }

        // Exponential backoff before retrying
        const delay = baseDelay * Math.pow(2, attempt - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
        // continue retrying
      }
    }
    return { ok: false, data: null, error: new Error("Unknown error") };
  }

  public async postSafe<T = any>(url: string, data?: any, config?: any): Promise<{ ok: boolean; data: T | null; error?: any }> {
    const maxAttempts = config?.retries ?? 2;
    let attempt = 0;
    const baseDelay = 300;
    while (attempt < maxAttempts) {
      try {
        const resp = await this.client.post<T>(url, data, config);
        return { ok: true, data: resp.data ?? null };
      } catch (error: any) {
        if (error?.code === "ERR_CANCELED" || error?.name === "CanceledError") {
          return { ok: false, data: null, error: { aborted: true } };
        }

        const status = error?.response?.status;
        if (status && status >= 400 && status < 500 && status !== 429) {
          console.error("API POST client error (non-retriable):", url, status);
          return { ok: false, data: null, error };
        }

        attempt += 1;
        if (attempt >= maxAttempts) {
          console.error("API POST error (safe):", url, error);
          return { ok: false, data: null, error };
        }

        const delay = baseDelay * Math.pow(2, attempt - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
    return { ok: false, data: null, error: new Error("Unknown error") };
  }
}

export const apiClient = new APIClient();
