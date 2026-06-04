import { api } from "./client";

export type SyncStatus = {
  last_sync_time: string | null;
  last_sync_status: string | null;
  files_indexed: number;
  repositories_indexed: number;
  memory_updates: number;
  active_sync_id: number | null;
  active_sync_status: string | null;
  progress_message: string | null;
  discovery_roots: string[];
  tracked_files: number;
  
  // New live progress state fields
  sync_status?: string | null;
  current_path?: string | null;
  total_files?: number;
  indexed?: number;
  pending?: number;
  errors?: number;
  progress_percent?: number;
  speed_files_per_sec?: number;
  estimated_time_remaining?: number;
  error_logs?: string[];
};

export type ScopeConfig = {
  include_folders: string[];
  exclude_folders: string[];
  priority_folders: string[];
  ignore_patterns: string[];
  auto_sync_enabled: boolean;
};

export type SyncRun = {
  id: number;
  status: string;
  started_at: string;
  completed_at: string | null;
  files_indexed: number;
  files_added: number;
  files_modified: number;
  files_removed: number;
  repositories_indexed: number;
  memory_updates: number;
  progress_message: string | null;
  result_summary: string | null;
};

export type AutomationSettings = {
  automation_level: "observation" | "approval" | "trusted";
  trusted_categories: string[];
  observer_enabled: boolean;
};

export type ProactiveNotification = {
  id: number;
  priority: string;
  title: string;
  message: string;
  action_type: string | null;
  action_payload: Record<string, unknown>;
  created_at: string;
};

export type RepositoryProfile = {
  path: string;
  name: string;
  summary: string;
  architecture_summary: string;
  tech_stack: string;
  dependencies: string[];
  entry_points: string[];
  important_files: string[];
  updated_at: string;
};

export async function getSyncStatus(): Promise<SyncStatus> {
  const res = await api.get("/sync/status");
  return res.data;
}

export async function triggerSyncNow(): Promise<SyncRun> {
  const res = await api.post("/sync/now");
  return res.data;
}

export async function getLatestSyncRun(): Promise<SyncRun | null> {
  const res = await api.get("/sync/runs/latest");
  return res.data;
}

export async function getSyncRun(runId: number): Promise<SyncRun> {
  const res = await api.get(`/sync/runs/${runId}`);
  return res.data;
}

export async function pauseSync(): Promise<void> {
  await api.post("/sync/pause");
}

export async function resumeSync(): Promise<void> {
  await api.post("/sync/resume");
}

export async function cancelSync(): Promise<void> {
  await api.post("/sync/cancel");
}

export async function forceResync(): Promise<SyncRun> {
  const res = await api.post("/sync/force");
  return res.data;
}

export async function getScopeConfig(): Promise<ScopeConfig> {
  const res = await api.get("/sync/config");
  return res.data;
}

export async function addIncludeFolder(path: string): Promise<void> {
  await api.post("/sync/config/include", { path });
}

export async function addExcludeFolder(path: string): Promise<void> {
  await api.post("/sync/config/exclude", { path });
}

export async function removeIncludeFolder(path: string): Promise<void> {
  await api.post("/sync/config/include/remove", { path });
}

export async function removeExcludeFolder(path: string): Promise<void> {
  await api.post("/sync/config/exclude/remove", { path });
}

export async function getAutomationSettings(): Promise<AutomationSettings> {
  const res = await api.get("/intelligence/settings/automation");
  return res.data;
}

export async function updateAutomationSettings(
  payload: Partial<AutomationSettings>
): Promise<AutomationSettings> {
  const res = await api.put("/intelligence/settings/automation", payload);
  return res.data;
}

export async function getProactiveNotifications(): Promise<ProactiveNotification[]> {
  const res = await api.get("/intelligence/proactive");
  return res.data;
}

export async function dismissProactiveNotification(id: number): Promise<void> {
  await api.post(`/intelligence/proactive/${id}/dismiss`);
}

export async function listRepositoryProfiles(): Promise<RepositoryProfile[]> {
  const res = await api.get("/intelligence/repositories");
  return res.data;
}
