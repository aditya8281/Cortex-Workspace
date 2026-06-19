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
  programming_languages?: string[];
  frameworks?: string[];
  current_projects?: { name: string; description?: string }[];
  contribution_style?: string | null;
  social_links?: { twitter?: string; linkedin?: string; website?: string };
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
  programming_languages?: string[];
  frameworks?: string[];
  current_projects?: { name: string; description: string }[];
  contribution_style?: string;
  social_links?: { twitter?: string; linkedin?: string; website?: string };
  preferences?: Record<string, unknown>;
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
  tags: string[];
  embedding_id: string | null;
  vector_collection: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MemorySearchResult {
  score: number;
  id: number;
  user_id: number | null;
  category: string;
  title: string;
  content: string;
  source_path: string | null;
  tags: string[];
  embedding_id: string | null;
  vector_collection: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MemoryListResponse {
  timestamp: string;
  count: number;
  total?: number;
  offset?: number;
  limit?: number;
  categories: Record<string, number>;
  entries: MemoryEntry[];
}

export interface MemorySearchResponse {
  query: string;
  results: MemorySearchResult[];
}

// ── System ──────────────────────────────────────────────────────

export interface SystemMetrics {
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  gpu_name: string;
  gpu_type: string;
  gpu_percent: number | null;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
}

export interface SystemLog {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  request_id: string;
  module: string;
  pathname: string;
  lineno: number;
}

export interface SystemLogsResponse {
  logs: SystemLog[];
  total: number;
}

// ── Notifications ───────────────────────────────────────────────

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}
