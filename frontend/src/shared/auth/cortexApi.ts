/**
 * Cortex API Client — Auth, Memory, Profile, GitHub, Vault, and CRTX.
 * All requests go directly to the backend (CORS configured on backend).
 * httpOnly cookies are set by the backend for its own origin.
 */

import type {
  User,
  TokenResponse,
  UsernameCheckResponse,
  ProfileUpdate,
  GitHubStatus,
  VaultStatus,
  VaultFileEntry,
  VaultUploadResult,
  CrtxVerifyResult,
  CrtxImportResult,
  MemoryEntry,
  MemoryListResponse,
  MemorySearchResponse,
} from "../types";

/** Backend base URL — requests go directly to the backend, not through proxy. */
function getBase(): string {
  const env = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && /^https?:\/\//.test(env)) {
    return env.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  }
  return "http://localhost:8000";
}

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
      const res = await fetch(`${getBase()}/api/auth/refresh`, {
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

async function request<T = unknown>(
  method: string,
  path: string,
  { body, headers: extraHeaders }: RequestOptions = {},
  _retried = false,
): Promise<T> {
  const url = `${getBase()}${path}`;
  const bodyString = body !== undefined ? JSON.stringify(body) : undefined;

  const res = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...extraHeaders,
    },
    body: bodyString,
    credentials: "include",
  });

  if (res.status === 401 && !_retried && !path.includes("/api/auth/")) {
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

// ── Auth endpoints ──────────────────────────────────────────────────

export function apiLogin(payload: {
  username: string;
  password: string;
}): Promise<TokenResponse> {
  return request("POST", "/api/auth/login", { body: payload });
}

export function apiRegister(payload: {
  username: string;
  password: string;
  confirm_password: string;
  full_name: string;
  nickname: string;
  bio?: string;
  vault_password: string;
  storage_root?: string;
}): Promise<TokenResponse> {
  return request("POST", "/api/auth/register", { body: payload });
}

export function apiGetMe(): Promise<User> {
  return request("GET", "/api/auth/me");
}

export function apiLogout(): Promise<unknown> {
  return request("POST", "/api/auth/logout", {
    body: { refresh_token: "" },
  });
}

export function apiRefresh(): Promise<TokenResponse> {
  return request("POST", "/api/auth/refresh", { body: { refresh_token: "" } });
}

export function apiCheckUsername(
  username: string
): Promise<UsernameCheckResponse> {
  return request("POST", "/api/auth/check-username", { body: { username } });
}

// ── Profile endpoints ───────────────────────────────────────────────

export function apiUpdateProfile(payload: ProfileUpdate): Promise<User> {
  return request("PUT", "/api/v1/me/profile", { body: payload });
}

export async function apiUploadAvatar(
  file: File
): Promise<{ profile_photo: string }> {
  const fd = new FormData();
  fd.append("file", file);
  let res = await fetch(`${getBase()}/api/v1/me/profile/photo`, {
    method: "POST",
    credentials: "include",
    body: fd,
  });
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(`${getBase()}/api/v1/me/profile/photo`, {
        method: "POST",
        credentials: "include",
        body: fd,
      });
    }
  }
  let data: { profile_photo?: string; detail?: string } | null = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const msg = data?.detail ?? `Upload failed (${res.status})`;
    throw new Error(msg);
  }
  return data as { profile_photo: string };
}

export function apiRemoveAvatar(): Promise<{ profile_photo: null }> {
  return request("DELETE", "/api/v1/me/profile/photo");
}

/**
 * Return the public URL for a user's profile photo.
 * Uses the /photo/{user_id} endpoint (no auth needed for <img> tags).
 */
export function getProfilePhotoUrl(userId: number): string {
  return `/api/v1/me/profile/photo/${userId}`;
}

// ── GitHub endpoints ────────────────────────────────────────────────

export function apiConnectGitHub(
  username: string,
  ghToken: string,
): Promise<GitHubStatus> {
  return request("POST", "/api/v1/me/github", {
    body: { username, token: ghToken },
  });
}

export function apiDisconnectGitHub(): Promise<GitHubStatus> {
  return request("DELETE", "/api/v1/me/github");
}

// ── Vault endpoints ─────────────────────────────────────────────────

export function apiVaultStatus(): Promise<VaultStatus> {
  return request("GET", "/api/v1/me/vault/status");
}

export function apiVaultUnlock(
  password: string
): Promise<{ unlocked: boolean; message: string }> {
  return request("POST", "/api/v1/me/vault/unlock", {
    body: { vault_password: password },
  });
}

export function apiVaultLock(): Promise<{ locked: boolean; message: string }> {
  return request("POST", "/api/v1/me/vault/lock");
}

export function apiVaultListFiles(
  folder = "/",
  recursive = false
): Promise<VaultFileEntry[]> {
  return request(
    "GET",
    `/api/v1/me/vault/files?folder=${encodeURIComponent(folder)}&recursive=${recursive}`
  );
}

export async function apiVaultUploadFile(
  file: File,
  folder = "/"
): Promise<VaultUploadResult> {
  const fd = new FormData();
  fd.append("file", file);
  const uploadUrl = `${getBase()}/api/v1/me/vault/files/upload?folder=${encodeURIComponent(folder)}`;
  let res = await fetch(uploadUrl, {
    method: "POST",
    credentials: "include",
    body: fd,
  });
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(uploadUrl, {
        method: "POST",
        credentials: "include",
        body: fd,
      });
    }
  }
  let data: VaultUploadResult | { detail?: string } | null = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const msg =
      (data as { detail?: string } | null)?.detail ??
      `Upload failed (${res.status})`;
    throw new Error(msg);
  }
  return data as VaultUploadResult;
}

export function apiVaultDeleteFile(
  filePath: string
): Promise<{ deleted: boolean }> {
  return request(
    "DELETE",
    `/api/v1/me/vault/files/${encodeURIComponent(filePath)}`
  );
}

export function apiVaultCreateFolder(
  folderPath: string
): Promise<{ name: string; path: string }> {
  return request("POST", "/api/v1/me/vault/folders", {
    body: { folder_path: folderPath },
  });
}

export function apiVaultRenameItem(
  filePath: string,
  newName: string
): Promise<{ name: string; path: string }> {
  return request(
    "PUT",
    `/api/v1/me/vault/files/${encodeURIComponent(filePath)}/rename`,
    {
      body: { new_name: newName },
    }
  );
}

export function apiVaultMoveFile(
  sourcePath: string,
  destinationFolder: string
): Promise<{ name: string; path: string }> {
  return request("POST", "/api/v1/me/vault/files/move", {
    body: { source_path: sourcePath, destination_folder: destinationFolder },
  });
}

export function apiVaultUpdateMetadata(
  filePath: string,
  payload: { favorite?: boolean; tags?: string[] }
): Promise<{ path: string; favorite: boolean; tags: string[] }> {
  return request(
    "PUT",
    `/api/v1/me/vault/files/${encodeURIComponent(filePath)}/metadata`,
    {
      body: payload,
    }
  );
}

export function apiVaultExport(payload: {
  paths: string[];
  destination_dir: string;
}): Promise<{ exported: boolean; count: number }> {
  return request("POST", "/api/v1/me/vault/files/export", {
    body: payload,
  });
}

export function apiVaultChangePassword(payload: {
  old_password: string;
  new_password: string;
}): Promise<{ message: string }> {
  return request("POST", "/api/v1/me/vault/change-password", {
    body: payload,
  });
}

export async function apiVaultPreviewFile(filePath: string): Promise<Blob> {
  const previewUrl = `${getBase()}/api/v1/me/vault/files/preview/${encodeURIComponent(filePath)}`;
  let res = await fetch(previewUrl, { method: "GET", credentials: "include" });
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(previewUrl, { method: "GET", credentials: "include" });
    }
  }
  if (!res.ok) throw new Error(`Preview failed (${res.status})`);
  return res.blob();
}

export async function apiVaultDownloadFileBlob(filePath: string): Promise<Blob> {
  const dlUrl = `${getBase()}/api/v1/me/vault/files/download/${encodeURIComponent(filePath)}`;
  let res = await fetch(dlUrl, { method: "GET", credentials: "include" });
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await fetch(dlUrl, { method: "GET", credentials: "include" });
    }
  }
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  return res.blob();
}

// ── CRTX Export/Import endpoints (DISABLED — backend routes inactive) ──

/** @deprecated CRTX routes are disabled. This function will always throw. */
export function apiCrtxVerify(_file: File): Promise<CrtxVerifyResult> {
  return Promise.reject(new Error("CRTX export/import is not yet available"));
}

/** @deprecated CRTX routes are disabled. This function will always throw. */
export function apiCrtxImport(
  _file: File,
  _exportPassword: string,
  _newStorageRoot: string
): Promise<CrtxImportResult> {
  return Promise.reject(new Error("CRTX export/import is not yet available"));
}

// ── Memory endpoints ────────────────────────────────────────────────

export function apiListMemory(params: {
  limit?: number;
  offset?: number;
  category?: string;
} = {}): Promise<MemoryListResponse> {
  const query = new URLSearchParams();
  if (params.limit) query.set("limit", String(params.limit));
  if (params.offset) query.set("offset", String(params.offset));
  if (params.category) query.set("category", params.category);
  const qs = query.toString();
  return request("GET", `/api/memory${qs ? `?${qs}` : ""}`);
}

export function apiCreateMemory(payload: {
  title: string;
  content: string;
  category?: string;
  source_path?: string;
  tags?: string[];
}): Promise<{ status: string; entry: MemoryEntry }> {
  return request("POST", "/api/memory", { body: payload });
}

export function apiGetMemory(id: number): Promise<MemoryEntry> {
  return request("GET", `/api/memory/${id}`);
}

export function apiUpdateMemory(
  id: number,
  payload: {
    title?: string;
    content?: string;
    category?: string;
    source_path?: string;
    tags?: string[];
  },
): Promise<{ status: string; entry: MemoryEntry }> {
  return request("PUT", `/api/memory/${id}`, { body: payload });
}

export function apiDeleteMemory(
  id: number,
): Promise<{ status: string }> {
  return request("DELETE", `/api/memory/${id}`);
}

export function apiSearchMemory(payload: {
  query: string;
  limit?: number;
}): Promise<MemorySearchResponse> {
  return request("POST", "/api/memory/search", { body: payload });
}

export function apiScanRepo(repoPath: string): Promise<{ status: string; job_id: string | null }> {
  return request("POST", "/api/memory/scan-repo", { body: { repo_path: repoPath } });
}

// ── Account deletion ────────────────────────────────────────────────

export async function apiDeleteAccount(
  password: string
): Promise<{ message: string }> {
  const res = await fetch(`${getBase()}/api/auth/me`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Delete failed");
  }
  return res.json();
}

// ── Admin endpoints ─────────────────────────────────────────────────

export function apiListUsers(): Promise<User[]> {
  return request("GET", "/api/v1/users");
}

export function apiPromoteUser(userId: number): Promise<User> {
  return request("POST", `/api/v1/users/${userId}/promote`);
}

export function apiDemoteUser(userId: number): Promise<User> {
  return request("POST", `/api/v1/users/${userId}/demote`);
}

export function apiDeleteUser(
  userId: number
): Promise<{ message: string }> {
  return request("DELETE", `/api/v1/users/${userId}`);
}
