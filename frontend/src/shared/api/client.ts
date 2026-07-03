"use client";

const API_BASE = "/api/v1";

/**
 * Read CSRF token fresh from cookie on every request.
 * Backend rotates the cortex_csrf cookie on every GET response,
 * so caching the value causes stale tokens → 403.
 */
export function getCsrfToken(): string {
  const match = document.cookie.match(/cortex_csrf=([^;]+)/);
  return match?.[1] ?? "";
}

/**
 * Direct backend URL for SSE/streaming connections.
 * Uses build-time env (inlined) or falls back to localhost:8000.
 * Bypasses Next.js proxy which buffers streaming responses.
 */
const BACKEND_URL =
  (typeof process !== "undefined" && (process.env as any).NEXT_PUBLIC_CORTEX_BACKEND_URL) ||
  "http://localhost:8000";

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: Record<string, unknown> | unknown[] | null;
}

/**
 * Shared fetch wrapper with CSRF and 401 refresh.
 * _retryDepth prevents infinite recursion when the refresh
 * itself returns a 401 or the new cookie isn't available yet.
 */
const MAX_RETRIES = 1;

/**
 * Shared refresh promise so concurrent 401s only fire ONE refresh request.
 * The second 401 waits for the first refresh to complete, then retries.
 */
let refreshPromise: Promise<Response> | null = null;

async function doRefresh(): Promise<Response> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  }).finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

/** Auth endpoints where 401 = bad credentials, not expired session */
function isAuthPath(path: string): boolean {
  return (
    path.startsWith("/auth/login") ||
    path.startsWith("/auth/register") ||
    path.startsWith("/auth/check-username") ||
    path.startsWith("/auth/logout")
  );
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const {
    method = "GET",
    headers: customHeaders,
    body,
    ...rest
  } = options as ApiFetchOptions & { _retryDepth?: number };

  const retryDepth = (options as any)._retryDepth ?? 0;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders as Record<string, string>),
  };

  if (method !== "GET") {
    headers["X-CSRF-Token"] = getCsrfToken();
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
    ...rest,
  });

  // On auth endpoints, 401 means wrong credentials — don't intercept
  if (res.status === 401 && !isAuthPath(path)) {
    if (retryDepth >= MAX_RETRIES) {
      window.location.href = "/auth";
      throw new Error("Session expired");
    }

    try {
      const refreshRes = await doRefresh();

      if (refreshRes.ok) {
        return apiFetch<T>(path, {
          ...options,
          _retryDepth: retryDepth + 1,
        } as any);
      }
    } catch {
      // refresh itself failed — fall through to redirect
    }

    window.location.href = "/auth";
    throw new Error("Session expired");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Request failed");
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

/**
 * Low-level streaming fetch that handles CSRF + 401 refresh.
 * Returns the raw Response so the caller can read the SSE stream.
 */
export async function apiFetchStream(
  path: string,
  options: ApiFetchOptions = {},
): Promise<Response> {
  const {
    method = "GET",
    headers: customHeaders,
    body,
    ...rest
  } = options as ApiFetchOptions & { _retryDepth?: number };

  const retryDepth = (options as any)._retryDepth ?? 0;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders as Record<string, string>),
  };

  if (method !== "GET") {
    headers["X-CSRF-Token"] = getCsrfToken();
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
    ...rest,
  });

  if (res.status === 401 && !isAuthPath(path)) {
    if (retryDepth >= MAX_RETRIES) {
      window.location.href = "/auth";
      throw new Error("Session expired");
    }

    try {
      const refreshRes = await doRefresh();

      if (refreshRes.ok) {
        return apiFetchStream(path, {
          ...options,
          _retryDepth: retryDepth + 1,
        } as any);
      }
    } catch {
      // fall through
    }

    window.location.href = "/auth";
    throw new Error("Session expired");
  }

  return res;
}
