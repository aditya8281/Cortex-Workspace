/**
 * Cortex API Client — Auth, Memory, and Profile.
 * Resolves backend origin dynamically and injects auth headers.
 */

const API_VERSION = "/api/v1";

/** Resolve the backend base URL. */
function getBase() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envBase && /^https?:\/\//.test(envBase)) {
    return envBase.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  }
  return "";
}

let _tokenFn = null;

/** Called by AuthProvider to provide the current token. */
export function setTokenProvider(fn) {
  _tokenFn = fn;
}

function authHeaders() {
  const token = _tokenFn?.();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(method, path, { body, headers: extraHeaders } = {}) {
  const url = `${getBase()}${path}`;
  const res = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...extraHeaders,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const msg = data?.detail || data?.error || `Request failed (${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.body = data;
    throw err;
  }

  return data;
}

// ── Auth endpoints ──────────────────────────────────────────────────

export function apiLogin(payload) {
  return request("POST", "/api/auth/login", { body: payload });
}

export function apiRegister(payload) {
  return request("POST", "/api/auth/register", { body: payload });
}

export function apiGetMe() {
  return request("GET", "/api/auth/me");
}

export function apiLogout(refreshToken) {
  return request("POST", "/api/auth/logout", { body: { refresh_token: refreshToken } });
}

// ── Profile endpoints ───────────────────────────────────────────────

export function apiGetProfile() {
  return request("GET", "/api/v1/me/profile");
}

export function apiUpdateProfile(payload) {
  return request("PUT", "/api/v1/me/profile", { body: payload });
}

export async function apiUploadAvatar(file) {
  const fd = new FormData();
  fd.append("file", file);
  const url = `${getBase()}/api/v1/me/profile/photo`;
  const res = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const msg = data?.detail || `Upload failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

export function apiRemoveAvatar() {
  return request("DELETE", "/api/v1/me/profile/photo");
}

/**
 * Return the public URL for a user's profile photo.
 * Uses the /photo/{user_id} endpoint (no auth needed for <img> tags).
 */
export function getProfilePhotoUrl(userId) {
  return `${getBase()}/api/v1/me/profile/photo/${userId}`;
}
