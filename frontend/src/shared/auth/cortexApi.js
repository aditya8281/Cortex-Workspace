/**
 * Cortex Auth & Profile API Layer
 * Communicates through the Next.js proxy routes and directly to /api/v1 endpoints.
 */

import { PUBLIC_BASE } from "../apiClient";

// token provider and auth error handler can be set by AuthProvider
let _tokenProvider = null;
let _authErrorHandler = null;

export function setTokenProvider(fn) {
  _tokenProvider = fn;
}

export function setAuthErrorHandler(fn) {
  _authErrorHandler = fn;
}

function authHeader() {
  try {
    const token = _tokenProvider ? _tokenProvider() : null;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch (e) {
    return {};
  }
}

async function handleResponse(res) {
  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const message = data?.detail || data?.error || `Request failed (${res.status})`;
    const err = new Error(message);
    err.status = res.status;
    err.body = data;
    // global 401 handling
    if (res.status === 401 && typeof _authErrorHandler === "function") {
      try { _authErrorHandler(); } catch (e) {}
    }
    throw err;
  }
  return data;
}

export async function apiLogin({ username, password }) {
  const res = await fetch(makeUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(res);
}

export async function apiRegister(payload) {
  const res = await fetch(makeUrl("/api/auth/register"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiGetMe() {
  const res = await fetch(makeUrl("/api/auth/me"), {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  return handleResponse(res);
}

export async function apiUpdateMe(payload) {
  const res = await fetch(makeUrl("/api/auth/me"), {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiGetProfile() {
  const res = await fetch(makeUrl("/api/v1/me/profile"), {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  return handleResponse(res);
}

export async function apiUpdateProfile(payload) {
  const res = await fetch(makeUrl("/api/v1/me/profile"), {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiUpdatePreferences(payload) {
  const res = await fetch(makeUrl("/api/v1/me/profile/preferences"), {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiUploadProfilePhoto(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(makeUrl("/api/v1/me/profile/photo"), {
    method: "POST",
    headers: { ...(authHeader() || {}) },
    body: fd,
  });
  return handleResponse(res);
}

export async function apiDeleteProfilePhoto() {
  const res = await fetch(makeUrl("/api/v1/me/profile/photo"), {
    method: "DELETE",
    headers: { ...authHeader() },
  });
  return handleResponse(res);
}

export async function apiChangePassword(payload) {
  const res = await fetch(makeUrl("/api/v1/me/profile/change-password"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiChangeVaultPassword(payload) {
  const res = await fetch(makeUrl("/api/v1/me/profile/change-vault-password"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

// Return a URL clients can use to GET the current user's profile photo
export function apiGetProfilePhotoUrl() {
  return makeUrl("/api/v1/me/profile/photo");
}

function makeUrl(path) {
  const base = PUBLIC_BASE || null;
  // If PUBLIC_BASE is absolute (http://...), call backend directly
  if (base && (/^https?:\/\//.test(base) || base.startsWith("//"))) {
    const normalized = base.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
    return `${normalized}${path}`;
  }

  // If running in the browser during development and no PUBLIC_BASE provided,
  // assume backend is on localhost:8000 so client requests reach the FastAPI server
  if (typeof window !== "undefined") {
    try {
      // Allow an override if the page sets a global
      const override = window.__CORTEX_BACKEND_ORIGIN__;
      if (override && (/^https?:\/\//.test(override) || override.startsWith("//"))) {
        return `${override.replace(/\/$/, "")}${path}`;
      }

      // Default development backend origin
      const host = window.location.hostname || 'localhost';
      const backendOrigin = host === 'localhost' ? 'http://localhost:8000' : `${window.location.protocol}//${host}:8000`;
      return `${backendOrigin}${path}`;
    } catch (e) {
      return path;
    }
  }

  // Otherwise rely on relative path (server-side rendering or production proxy)
  return path;
}
