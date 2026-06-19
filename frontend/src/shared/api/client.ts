/**
 * Base HTTP client for Cortex API.
 * All requests go through this client with automatic token refresh and CSRF handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

interface RequestError extends Error {
  status?: number;
  body?: unknown;
}

interface RequestOptions {
  body?: unknown;
  headers?: Record<string, string>;
}

let _refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ refresh_token: "" }),
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();
  return _refreshPromise;
}

function getCsrfToken(): string | undefined {
  return document.cookie
    .split("; ")
    .find((c) => c.startsWith("cortex_csrf="))
    ?.split("=")[1];
}

async function request<T = unknown>(
  method: string,
  path: string,
  { body, headers: extraHeaders }: RequestOptions = {},
  _retried = false,
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const bodyString = body !== undefined ? JSON.stringify(body) : undefined;

  const csrfToken = getCsrfToken();

  const res = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "x-csrf-token": csrfToken } : {}),
      ...extraHeaders,
    },
    body: bodyString,
    credentials: "include",
  });

  if (res.status === 401 && !_retried && !path.match(/\/api\/v1\/auth\/(login|register|refresh|logout|check-username)/)) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return request<T>(method, path, { body, headers: extraHeaders }, true);
    }
  }

  let data: Record<string, unknown> | null = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail = (data as Record<string, unknown> | null)?.detail;
    const error = (data as Record<string, unknown> | null)?.error;
    const msg =
      (typeof detail === "string" ? detail : null) ??
      (typeof error === "string" ? error : null) ??
      `Request failed (${res.status})`;
    const err: RequestError = new Error(msg);
    err.status = res.status;
    err.body = data;
    throw err;
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, { body }),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, { body }),
  delete: <T>(path: string) => request<T>("DELETE", path),
};

export { getCsrfToken, tryRefresh };
