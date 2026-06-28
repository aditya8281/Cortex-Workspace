/**
 * Privacy API Client — v1.05 Privacy & Trust
 *
 * Covers: Vault, Access Control, Audit, Consent, Export, Settings, Transparency
 * Backend routes: /api/v1/privacy/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface VaultStatus {
  locked: boolean;
  encrypted: boolean;
  file_count: number;
  total_size: number;
  last_accessed: string;
}

export interface VaultFile {
  path: string;
  name: string;
  size: number;
  mime_type: string;
  created_at: string;
  modified_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
  user_agent: string;
  success: boolean;
  error_details: string | null;
  created_at: string;
}

export interface ConsentEntry {
  id: number;
  scope: string;
  granted: boolean;
  granted_at: string;
  revoked_at: string | null;
}

export interface Role {
  id: number;
  name: string;
  permissions: string[];
}

export interface Permission {
  id: number;
  name: string;
  description: string;
  resource: string;
  action: string;
}

export interface UsageStats {
  total_requests: number;
  requests_by_endpoint: Record<string, number>;
  requests_by_hour: Record<string, number>;
  active_users: number;
}

export interface StorageUsage {
  total_bytes: number;
  by_type: Record<string, number>;
  vault_bytes: number;
  database_bytes: number;
}

export interface ModelSettings {
  default_model: string;
  temperature: number;
  max_tokens: number;
  streaming: boolean;
}

// ── Vault ──────────────────────────────────────────────────────────────────

export const vault = {
  unlock: (data: { password: string }) =>
    apiFetch<{ unlocked: boolean; token: string }>("/privacy/vault/unlock", { method: "POST", body: data }),

  lock: () =>
    apiFetch<{ locked: boolean }>("/privacy/vault/lock", { method: "POST" }),

  status: () =>
    apiFetch<VaultStatus>("/privacy/vault/status"),

  files: () =>
    apiFetch<{ items: VaultFile[] }>("/privacy/vault/files"),

  upload: (data: FormData) =>
    fetch("/api/v1/privacy/vault/files/upload", {
      method: "POST",
      headers: { "X-CSRF-Token": document.cookie.match(/cortex_csrf=([^;]+)/)?.[1] ?? "" },
      credentials: "include",
      body: data,
    }).then((r) => r.json()) as Promise<{ path: string; name: string }>,

  preview: (filePath: string) =>
    apiFetch<{ content: string; mime_type: string }>(`/privacy/vault/files/preview/${encodeURIComponent(filePath)}`),

  download: (filePath: string) =>
    fetch(`/api/v1/privacy/vault/files/download/${encodeURIComponent(filePath)}`, {
      credentials: "include",
    }),

  delete: (filePath: string) =>
    apiFetch<{ deleted: boolean }>(`/privacy/vault/files/${encodeURIComponent(filePath)}`, { method: "DELETE" }),

  rename: (filePath: string, data: { new_name: string }) =>
    apiFetch<{ renamed: boolean }>(`/privacy/vault/files/${encodeURIComponent(filePath)}/rename`, { method: "PUT", body: data }),

  move: (data: { file_path: string; destination: string }) =>
    apiFetch<{ moved: boolean }>("/privacy/vault/files/move", { method: "POST", body: data }),

  metadata: (filePath: string, data: Record<string, any>) =>
    apiFetch<{ updated: boolean }>(`/privacy/vault/files/${encodeURIComponent(filePath)}/metadata`, { method: "PUT", body: data }),

  createFolder: (data: { name: string; parent?: string }) =>
    apiFetch<{ path: string }>("/privacy/vault/folders", { method: "POST", body: data }),

  search: (data: { query: string }) =>
    apiFetch<{ items: VaultFile[] }>("/privacy/vault/search", { method: "POST", body: data }),

  export: (data: { paths?: string[] }) =>
    apiFetch<{ export_id: string; status: string }>("/privacy/vault/files/export", { method: "POST", body: data }),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiFetch<{ changed: boolean }>("/privacy/vault/change-password", { method: "POST", body: data }),
};

// ── Access Control ─────────────────────────────────────────────────────────

export const accessControl = {
  check: (params: { resource: string; action: string }) =>
    apiFetch<{ allowed: boolean }>(`/privacy/access-control/check?resource=${params.resource}&action=${params.action}`),

  roles: () =>
    apiFetch<{ items: Role[] }>("/privacy/access-control/roles"),

  permissions: () =>
    apiFetch<{ items: Permission[] }>("/privacy/access-control/permissions"),

  assignRole: (data: { user_id: number; role: string }) =>
    apiFetch<{ assigned: boolean }>("/privacy/access-control/roles/assign", { method: "POST", body: data }),

  removeRole: (data: { user_id: number; role: string }) =>
    apiFetch<{ removed: boolean }>("/privacy/access-control/roles/remove", { method: "POST", body: data }),
};

// ── Audit ──────────────────────────────────────────────────────────────────

export const audit = {
  logs: (params?: { limit?: number; action?: string; user_id?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.action) searchParams.set("action", params.action);
    if (params?.user_id) searchParams.set("user_id", String(params.user_id));
    const qs = searchParams.toString();
    return apiFetch<{ items: AuditLog[] }>(`/privacy/audit/logs${qs ? `?${qs}` : ""}`);
  },

  count: (params?: { action?: string; user_id?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.action) searchParams.set("action", params.action);
    if (params?.user_id) searchParams.set("user_id", String(params.user_id));
    const qs = searchParams.toString();
    return apiFetch<{ count: number }>(`/privacy/audit/logs/count${qs ? `?${qs}` : ""}`);
  },

  activity: (params?: { limit?: number }) => {
    const qs = params?.limit ? `?limit=${params.limit}` : "";
    return apiFetch<{ items: any[] }>(`/privacy/audit/activity${qs}`);
  },
};

// ── Consent ────────────────────────────────────────────────────────────────

export const consent = {
  list: () =>
    apiFetch<{ items: ConsentEntry[] }>("/privacy/consent"),

  check: (params: { scope: string }) =>
    apiFetch<{ granted: boolean }>(`/privacy/consent/check?scope=${params.scope}`),

  grant: (data: { scope: string }) =>
    apiFetch<ConsentEntry>("/privacy/consent/grant", { method: "POST", body: data }),

  revoke: (data: { scope: string }) =>
    apiFetch<{ revoked: boolean }>("/privacy/consent/revoke", { method: "POST", body: data }),
};

// ── Export ─────────────────────────────────────────────────────────────────

export const dataExport = {
  create: (data: { format: string; include?: string[] }) =>
    apiFetch<{ export_id: string; status: string }>("/privacy/export/create", { method: "POST", body: data }),

  process: (exportId: string) =>
    apiFetch<{ status: string; download_url: string }>(`/privacy/export/${exportId}/process`, { method: "POST" }),

  verify: (exportId: string) =>
    apiFetch<{ verified: boolean; checksum: string }>(`/privacy/export/${exportId}/verify`),
};

// ── Settings ───────────────────────────────────────────────────────────────

export const privacySettings = {
  usageStats: () =>
    apiFetch<UsageStats>("/privacy/models/usage/stats"),

  sync: () =>
    apiFetch<{ synced: boolean }>("/privacy/models/sync", { method: "POST" }),

  storage: () =>
    apiFetch<StorageUsage>("/privacy/models/storage"),

  updates: () =>
    apiFetch<{ items: any[] }>("/privacy/models/updates"),

  getSettings: () =>
    apiFetch<ModelSettings>("/privacy/models/settings"),

  updateSettings: (data: Partial<ModelSettings>) =>
    apiFetch<ModelSettings>("/privacy/models/settings", { method: "PUT", body: data }),

  refreshCatalogue: () =>
    apiFetch<{ refreshed: boolean }>("/privacy/models/catalogue/refresh", { method: "POST" }),
};

// ── Transparency ───────────────────────────────────────────────────────────

export const transparency = {
  explain: (data: { resource: string; action: string }) =>
    apiFetch<{ explanation: string; factors: string[] }>("/privacy/transparency/explain", { method: "POST", body: data }),

  templates: () =>
    apiFetch<{ items: any[] }>("/privacy/transparency/templates"),
};
