// API Middleware — Request/response interceptors
// Currently a placeholder. Populated when auth and error handling are implemented.

export interface RequestInterceptor {
  onRequest?: (config: RequestInit) => RequestInit | Promise<RequestInit>;
}

export interface ResponseInterceptor {
  onResponse?: (response: Response) => Response | Promise<Response>;
  onError?: (error: unknown) => unknown;
}

export function createApiMiddleware(
  interceptors: Array<RequestInterceptor | ResponseInterceptor>
): void {
  // Placeholder — will be integrated with apiClient in v1.03+
  void interceptors;
}
