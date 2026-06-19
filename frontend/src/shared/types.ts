/** Shared TypeScript types for the Cortex frontend. */

// ── User ──────────────────────────────────────────────────────────

export interface User {
  id: number;
  username: string | null;
  full_name: string;
  role: "user" | "admin";
  nickname: string;
  bio: string | null;
  description: string | null;
  profile_photo: string | null;
  handles: Record<string, unknown> | null;
  storage_root: string | null;
  github_username: string | null;
  data_path?: string | null;
  personal_storage_path?: string | null;
  preferences: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
}

// ── Auth ──────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  refresh_token?: string | null;
  user?: User | null;
}

export interface UsernameCheckResponse {
  available: boolean;
  message: string;
}

// ── Profile ───────────────────────────────────────────────────────

export interface ProfileUpdate {
  full_name?: string;
  nickname?: string;
  bio?: string;
  description?: string;
}

// ── GitHub ────────────────────────────────────────────────────────

export interface GitHubStatus {
  connected: boolean;
  github_username: string | null;
}

// ── Vault ─────────────────────────────────────────────────────────

export interface VaultStatus {
  locked: boolean;
  has_vault_password: boolean;
}

export interface VaultFileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified?: number;
  created?: number;
  favorite?: boolean;
  tags?: string[];
}

export interface VaultUploadResult {
  name: string;
  path: string;
  size: number;
}

// ── CRTX ──────────────────────────────────────────────────────────

export interface CrtxVerifyResult {
  metadata: Record<string, unknown>;
  manifest: Record<string, unknown>;
}

export interface CrtxImportResult {
  user_id: number;
  username: string;
  vault_files_restored: number;
  message: string;
}

// ── Memory ────────────────────────────────────────────────────────

export interface MemoryEntry {
  id: number;
  user_id: number | null;
  category: string;
  title: string;
  content: string;
  source_path: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MemoryListResponse {
  timestamp: string;
  count: number;
  categories: Record<string, number>;
  entries: MemoryEntry[];
}
