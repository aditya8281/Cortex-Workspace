/**
 * Cortex Auth & Profile API Layer
 * Communicates through the Next.js proxy routes and directly to /api/v1 endpoints.
 */

import { getSessionToken } from "./session";

function authHeader() {
  const token = getSessionToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
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
    throw err;
  }
  return data;
}

export async function apiLogin({ username, password }) {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(res);
}

export async function apiRegister(payload) {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiGetMe() {
  const res = await fetch("/api/auth/me", {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  return handleResponse(res);
}

export async function apiUpdateMe(payload) {
  const res = await fetch("/api/auth/me", {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function apiGetProfile() {
  const res = await fetch("/api/v1/me/profile", {
    headers: { "Content-Type": "application/json", ...authHeader() },
  });
  return handleResponse(res);
}

export async function apiUpdateProfile(payload) {
  const res = await fetch("/api/v1/me/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}
