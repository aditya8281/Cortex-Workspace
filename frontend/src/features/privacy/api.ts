/**
 * Privacy API Client — aligned with backend v1 privacy endpoints
 *
 * Covers: Vault, Access Control, Audit, Consent, Export, Settings, Transparency
 * Backend routes: /api/v1/privacy/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types (matching backend Pydantic schemas) ──────────────────────────────

export interface VaultStatus {
  locked: boolean;
  has_vault_password: boolean;
}

export interface VaultFile {
  name: string;
  path: string;
  is_dir: boolean;
  size: number | null;
  modified: number | null;
  created: number | null;
  favorite: boolean;
  tags: string[];
}

export interface AuditLog {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id: number | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  session_id: string | null;
  timestamp: string;
  success: number;
  error_message: string | null;
  duration_ms: number | null;
}

export interface ConsentEntry {
  id: number;
  user_id: number;
  consent_type: string;
  granted: number;
  scope: string | null;
  context: Record<string, any> | null;
  created_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  revoked_reason: string | null;
  version: number;
}

export interface Role {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Permission {
  id: number;
  resource_type: string;
  action: string;
  description: string | null;
}

export interface UsageStats {
  total_requests: number;
  requests_by_endpoint: Record<string, number>;
  requests_by_hour: Record<string, number>;
  active_users: number;
}

export interface StorageUsage {
  total_disk_gb: number;
  used_disk_gb: number;
  free_disk_gb: number;
  models_total_gb: number;
  models: any[];
  cache_gb: number;
}

export interface ModelSettings {
  inference_backend: string;
  huggingface_token: string | null;
  auto_download: boolean;
  max_concurrent_downloads: number;
}

// ── Vault ──────────────────────────────────────────────────────────────────

export const vault = {
  unlock: (data: { vault_password: string }) =>
    apiFetch<{ unlocked: boolean; message: string }>("/privacy/vault/unlock", { method: "POST", body: data }),

  lock: () =>
    apiFetch<{ locked: boolean; message: string }>("/privacy/vault/lock", { method: "POST" }),

  status: () =>
    apiFetch<VaultStatus>("/privacy/vault/status"),

  files: (folder?: string, recursive?: boolean) => {
    const qs = new URLSearchParams();
    if (folder) qs.set("folder", folder);
    if (recursive) qs.set("recursive", "true");
    const q = qs.toString();
    return apiFetch<VaultFile[]>(`/privacy/vault/files${q ? `?${q}` : ""}`);
  },

  upload: (data: FormData) =>
    fetch("/api/v1/privacy/vault/files/upload", {
      method: "POST",
      headers: { "X-CSRF-Token": document.cookie.match(/cortex_csrf=([^;]+)/)?.[1] ?? "" },
      credentials: "include",
      body: data,
    }).then((r) => r.json()) as Promise<{ path: string; name: string; size: number }>,

  preview: (filePath: string) =>
    fetch(`/api/v1/privacy/vault/files/preview/${encodeURIComponent(filePath)}`, {
      credentials: "include",
    }),

  download: (filePath: string) =>
    fetch(`/api/v1/privacy/vault/files/download/${encodeURIComponent(filePath)}`, {
      credentials: "include",
    }),

  delete: (filePath: string) =>
    apiFetch<{ deleted: boolean }>(`/privacy/vault/files/${encodeURIComponent(filePath)}`, { method: "DELETE" }),

  rename: (filePath: string, data: { new_name: string }) =>
    apiFetch<{ path: string; name: string }>(`/privacy/vault/files/${encodeURIComponent(filePath)}/rename`, { method: "PUT", body: data }),

  move: (data: { source_path: string; destination_folder: string }) =>
    apiFetch<{ name: string; path: string }>("/privacy/vault/files/move", { method: "POST", body: data }),

  metadata: (filePath: string, data: { favorite?: boolean; tags?: string[] }) =>
    apiFetch<{ path: string; favorite: boolean | null; tags: string[] | null }>(
      `/privacy/vault/files/${encodeURIComponent(filePath)}/metadata`, { method: "PUT", body: data },
    ),

  createFolder: (data: { folder_path: string }) =>
    apiFetch<{ path: string; name: string }>("/privacy/vault/folders", { method: "POST", body: data }),

  search: (data: { query: string }) =>
    apiFetch<{ results: Array<{ name: string; path: string; is_dir: boolean; score: number }> }>(
      "/privacy/vault/search", { method: "POST", body: data },
    ),

  export: (data: { paths: string[]; destination_dir: string }) =>
    apiFetch<{ exported: boolean; count: number }>("/privacy/vault/files/export", { method: "POST", body: data }),

  changePassword: (data: { old_password: string; new_password: string }) =>
    apiFetch<{ message: string }>("/privacy/vault/change-password", { method: "POST", body: data }),
};

// ── Access Control ─────────────────────────────────────────────────────────

export const accessControl = {
  check: (params: { resource_type: string; action: string }) =>
    apiFetch<{ allowed: boolean; resource_type: string; action: string; user_id: number }>(
      `/privacy/access-control/check?resource_type=${encodeURIComponent(params.resource_type)}&action=${encodeURIComponent(params.action)}`,
    ),

  roles: () =>
    apiFetch<Role[]>("/privacy/access-control/roles"),

  permissions: () =>
    apiFetch<Permission[]>("/privacy/access-control/permissions"),

  assignRole: (data: { target_user_id: number; name: string }) => {
    const qs = new URLSearchParams({ target_user_id: String(data.target_user_id) });
    return apiFetch<{ user_id: number; role: string; assigned: boolean }>(
      `/privacy/access-control/roles/assign?${qs}`, { method: "POST", body: { name: data.name } },
    );
  },

  removeRole: (data: { target_user_id: number; role_name: string }) => {
    const qs = new URLSearchParams({
      target_user_id: String(data.target_user_id),
      role_name: data.role_name,
    });
    return apiFetch<{ user_id: number; role: string; removed: boolean }>(
      `/privacy/access-control/roles/remove?${qs}`, { method: "POST" },
    );
  },
};

// ── Audit ──────────────────────────────────────────────────────────────────

export const audit = {
  logs: (params?: { limit?: number; offset?: number; action?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    if (params?.action) searchParams.set("action", params.action);
    const qs = searchParams.toString();
    return apiFetch<AuditLog[]>(`/privacy/audit/logs${qs ? `?${qs}` : ""}`);
  },

  count: () =>
    apiFetch<{ count: number }>("/privacy/audit/logs/count"),

  activity: (params?: { limit?: number }) => {
    const qs = params?.limit ? `?limit=${params.limit}` : "";
    return apiFetch<Array<{ id: number; action: string; resource_type: string; resource_id: string; timestamp: string }>>(
      `/privacy/audit/activity${qs}`,
    );
  },
};

// ── Consent ────────────────────────────────────────────────────────────────

export const consent = {
  list: () =>
    apiFetch<ConsentEntry[]>("/privacy/consent"),

  check: (params: { consent_type: string }) =>
    apiFetch<{ consent_type: string; granted: boolean }>(
      `/privacy/consent/check?consent_type=${encodeURIComponent(params.consent_type)}`,
    ),

  grant: (data: { consent_type: string; scope?: string; context?: Record<string, any> }) =>
    apiFetch<ConsentEntry>("/privacy/consent/grant", { method: "POST", body: data }),

  revoke: (data: { consent_type: string; reason?: string }) => {
    const qs = new URLSearchParams({ consent_type: data.consent_type });
    if (data.reason) qs.set("reason", data.reason);
    return apiFetch<{ consent_type: string; success: boolean }>(
      `/privacy/consent/revoke?${qs}`,
    );
  },
};

// ── Export ─────────────────────────────────────────────────────────────────

export const dataExport = {
  create: (data: { export_type: string; data_types?: string[]; format?: string }) =>
    apiFetch<any>("/privacy/export/create", { method: "POST", body: data }),

  process: (exportId: number) =>
    apiFetch<any>(`/privacy/export/${exportId}/process`, { method: "POST" }),

  verify: (exportId: number) =>
    apiFetch<{ verified: boolean; checksum: string }>(`/privacy/export/${exportId}/verify`),
};

// ── Settings ───────────────────────────────────────────────────────────────

export const privacySettings = {
  usageStats: () =>
    apiFetch<UsageStats>("/privacy/models/usage/stats"),

  sync: (provider?: string) => {
    const qs = provider ? `?provider=${encodeURIComponent(provider)}` : "";
    return apiFetch<{ job_id: string; status: string; models_discovered: number; models_added: number; models_updated: number; error_message: string | null }>(
      `/privacy/models/sync${qs}`, { method: "POST" },
    );
  },

  storage: () =>
    apiFetch<StorageUsage>("/privacy/models/storage"),

  updates: () =>
    apiFetch<{ updates: any[] }>("/privacy/models/updates"),

  getSettings: () =>
    apiFetch<ModelSettings>("/privacy/models/settings"),

  updateSettings: (data: Partial<ModelSettings>) =>
    apiFetch<ModelSettings>("/privacy/models/settings", { method: "PUT", body: data }),

  refreshCatalogue: () =>
    apiFetch<{ status: string; models_added: number }>("/privacy/models/catalogue/refresh", { method: "POST" }),
};

// ── Transparency ───────────────────────────────────────────────────────────

export const transparency = {
  explain: (data: { decision_type: string; context?: Record<string, any> }) =>
    apiFetch<Record<string, any>>("/privacy/transparency/explain", { method: "POST", body: data }),

  templates: () =>
    apiFetch<Record<string, any>>("/privacy/transparency/templates"),
};
