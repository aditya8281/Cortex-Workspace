"use client";

const API_BASE = "/api/v1";

let csrfToken: string | null = null;

function getCsrfToken(): string {
  if (csrfToken) return csrfToken;
  const match = document.cookie.match(/cortex_csrf=([^;]+)/);
  csrfToken = match?.[1] ?? "";
  return csrfToken;
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: Record<string, unknown> | unknown[] | null;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { method = "GET", headers: customHeaders, body, ...rest } = options;

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

  if (res.status === 401) {
    // Try refresh
    const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (refreshRes.ok) {
      // Retry original request
      return apiFetch<T>(path, options);
    }

    // Redirect to login
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
