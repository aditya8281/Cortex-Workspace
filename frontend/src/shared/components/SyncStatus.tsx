"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Check, Loader2, Settings, X, ChevronDown, FolderSync, Folder, Trash2, Plus } from "lucide-react";
import { api } from "@/shared/api/client";
import { syncApi } from "@/shared/api/sync";
import type { SyncDefaultPath, EmbeddingModelOption } from "@/shared/api/sync";
import { cn } from "../../lib/utils";

interface WatchedPath {
  path: string;
  repo_id: number | null;
  embedding_model: string;
  sync_enabled: boolean;
  initial_scan_job_id: string | null;
  initial_scan_status: string | null;
}

interface SyncStatusData {
  watching: number;
  pending_changes: number;
  indexed_files: number;
  errors: number;
  status: "idle" | "syncing" | "watching" | "indexing";
  last_sync: string | null;
  watched_paths: WatchedPath[];
}

interface SyncJobData {
  job_id: string;
  repo_path: string;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  total: number | null;
  result: { files_scanned?: number; chunks_created?: number } | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

const speedColors: Record<string, string> = {
  instant: "text-success",
  fast: "text-accent",
  medium: "text-warning",
  slow: "text-text-muted",
};

interface SyncSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStartSync: (repoPath: string, embeddingModel: string, excludeDirs: string[]) => Promise<void>;
  watchedPaths: WatchedPath[];
  onStopSync: (repoPath: string) => Promise<void>;
  onDeletePath: (repoPath: string) => void;
}

function SyncSettingsModal({
  open,
  onOpenChange,
  onStartSync,
  watchedPaths,
  onStopSync,
  onDeletePath,
}: SyncSettingsModalProps) {
  const [defaults, setDefaults] = useState<{
    defaultPaths: SyncDefaultPath[];
    excludeDirs: string[];
    embeddingModels: EmbeddingModelOption[];
  } | null>(null);
  const [loadingDefaults, setLoadingDefaults] = useState(true);

  const [selectedPaths, setSelectedPaths] = useState<Record<string, boolean>>({});
  const [customPath, setCustomPath] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("nomic-embed-text");
  const [excludeDirs, setExcludeDirs] = useState<string[]>([]);
  const [newExcludeDir, setNewExcludeDir] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showExcludeList, setShowExcludeList] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoadingDefaults(true);
    syncApi.defaults().then((data) => {
      setDefaults({
        defaultPaths: data.default_paths,
        excludeDirs: data.exclude_dirs,
        embeddingModels: data.embedding_models,
      });
      const initial: Record<string, boolean> = {};
      data.default_paths.forEach((p) => {
        initial[p.path] = p.enabled;
      });
      setSelectedPaths(initial);
      setExcludeDirs(data.exclude_dirs);
      setEmbeddingModel(data.embedding_models[0]?.value ?? "nomic-embed-text");
      setLoadingDefaults(false);
    }).catch(() => setLoadingDefaults(false));
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const pathsToSync = Object.entries(selectedPaths)
      .filter(([, enabled]) => enabled)
      .map(([path]) => path);

    if (customPath.trim()) {
      pathsToSync.push(customPath.trim());
    }

    if (pathsToSync.length === 0) {
      setError("Select at least one directory or enter a custom path");
      return;
    }

    setLoading(true);
    setError("");
    try {
      for (const path of pathsToSync) {
        await onStartSync(path, embeddingModel, excludeDirs);
      }
      setCustomPath("");
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start sync");
    } finally {
      setLoading(false);
    }
  };

  const addExcludeDir = () => {
    const dir = newExcludeDir.trim();
    if (dir && !excludeDirs.includes(dir)) {
      setExcludeDirs((prev) => [...prev, dir]);
      setNewExcludeDir("");
    }
  };

  const removeExcludeDir = (dir: string) => {
    setExcludeDirs((prev) => prev.filter((d) => d !== dir));
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-bg-elevated rounded-xl border border-border-subtle shadow-2xl w-full max-w-lg mx-4 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border-subtle shrink-0">
          <div className="flex items-center gap-2">
            <FolderSync size={16} className="text-accent" />
            <h2 className="text-sm font-semibold text-text">Auto-Sync Setup</h2>
          </div>
          <button
            onClick={() => onOpenChange(false)}
            className="text-text-muted hover:text-text transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {loadingDefaults ? (
          <div className="p-8 flex items-center justify-center">
            <Loader2 size={20} className="animate-spin text-accent" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 space-y-4 overflow-y-auto flex-1 min-h-0">
            {/* Default Directory Paths */}
            <div>
              <label className="block text-xs font-medium text-text-muted mb-2">
                Home Directories (auto-synced by default)
              </label>
              <div className="space-y-1.5">
                {defaults?.defaultPaths.map((dp) => (
                  <label
                    key={dp.path}
                    className={cn(
                      "flex items-center gap-3 p-2.5 rounded-lg border transition-all cursor-pointer",
                      selectedPaths[dp.path]
                        ? "border-accent/30 bg-accent/5"
                        : "border-border-subtle bg-bg-surface hover:border-border-default",
                      !dp.exists && "opacity-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={selectedPaths[dp.path] ?? false}
                      onChange={(e) =>
                        setSelectedPaths((prev) => ({
                          ...prev,
                          [dp.path]: e.target.checked,
                        }))
                      }
                      className="rounded border-border-subtle bg-bg-surface text-accent focus:ring-accent/20"
                      disabled={!dp.exists}
                    />
                    <Folder size={14} className={selectedPaths[dp.path] ? "text-accent" : "text-text-muted"} />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-medium text-text">{dp.label}</span>
                      <span className="text-[10px] text-text-muted ml-2 font-mono">{dp.path}</span>
                    </div>
                    {!dp.exists && (
                      <span className="text-[10px] text-text-muted italic">not found</span>
                    )}
                  </label>
                ))}
              </div>
            </div>

            {/* Custom Path */}
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1.5">
                Custom Directory
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customPath}
                  onChange={(e) => setCustomPath(e.target.value)}
                  placeholder="/path/to/your/project"
                  className="flex-1 px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
                />
              </div>
            </div>

            {/* Embedding Model */}
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1.5">
                Embedding Model
              </label>
              <div className="relative">
                <select
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle text-sm text-text appearance-none focus:outline-none focus:border-accent"
                >
                  {defaults?.embeddingModels.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} ({m.technique}, {m.dimensions}d)
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={14}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
                />
              </div>
              {/* Model description */}
              {defaults?.embeddingModels.find((m) => m.value === embeddingModel) && (
                <div className="mt-1.5 flex items-center gap-2">
                  <span className={cn("text-[10px] font-mono", speedColors[defaults.embeddingModels.find((m) => m.value === embeddingModel)!.speed] ?? "text-text-muted")}>
                    {defaults.embeddingModels.find((m) => m.value === embeddingModel)!.speed}
                  </span>
                  <span className="text-[10px] text-text-muted">
                    {defaults.embeddingModels.find((m) => m.value === embeddingModel)!.description}
                  </span>
                </div>
              )}
            </div>

            {/* Exclude Directories */}
            <div>
              <button
                type="button"
                onClick={() => setShowExcludeList(!showExcludeList)}
                className="flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors"
              >
                <Trash2 size={12} />
                Exclude Directories ({excludeDirs.length})
                <ChevronDown
                  size={12}
                  className={cn(
                    "transition-transform",
                    showExcludeList && "rotate-180"
                  )}
                />
              </button>
              {showExcludeList && (
                <div className="mt-2 space-y-2">
                  <div className="flex flex-wrap gap-1.5">
                    {excludeDirs.map((dir) => (
                      <span
                        key={dir}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-bg-surface border border-border-subtle text-[10px] font-mono text-text-muted"
                      >
                        {dir}
                        <button
                          type="button"
                          onClick={() => removeExcludeDir(dir)}
                          className="text-text-muted hover:text-error transition-colors"
                        >
                          <X size={10} />
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newExcludeDir}
                      onChange={(e) => setNewExcludeDir(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addExcludeDir();
                        }
                      }}
                      placeholder="Add directory to exclude"
                      className="flex-1 px-3 py-1.5 rounded-lg bg-bg-surface border border-border-subtle text-xs text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
                    />
                    <button
                      type="button"
                      onClick={addExcludeDir}
                      className="px-2 py-1.5 rounded-lg bg-bg-surface border border-border-subtle text-text-muted hover:text-text hover:border-border-default transition-colors"
                    >
                      <Plus size={12} />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <p className="text-xs text-error">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className={cn(
                "w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                "bg-accent text-white hover:bg-accent/90",
                "focus:outline-none focus:ring-2 focus:ring-accent/50",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              Start Auto-Sync
            </button>
          </form>
        )}

        {/* Watched Paths */}
        {watchedPaths.length > 0 && (
          <div className="p-4 border-t border-border-subtle shrink-0">
            <h3 className="text-xs font-medium text-text-muted mb-2">Currently Watched</h3>
            <div className="space-y-1.5 max-h-32 overflow-y-auto">
              {watchedPaths.map((wp) => (
                <div
                  key={wp.path}
                  className="flex items-center justify-between p-2 rounded-lg bg-bg-surface border border-border-subtle"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-text truncate">{wp.path}</p>
                    <p className="text-[10px] text-text-muted">{wp.embedding_model}</p>
                  </div>
                  <div className="flex items-center gap-2 ml-2">
                    {wp.initial_scan_status === "pending" || wp.initial_scan_status === "running" ? (
                      <Loader2 size={12} className="animate-spin text-accent" />
                    ) : wp.initial_scan_status === "completed" ? (
                      <Check size={12} className="text-success" />
                    ) : null}
                    <button
                      onClick={() => onDeletePath(wp.path)}
                      className="text-text-muted hover:text-error transition-colors"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Button({
  variant = "secondary",
  size = "sm",
  loading = false,
  className = "",
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  loading?: boolean;
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-all",
        "focus:outline-none focus:ring-2 focus:ring-accent/50",
        {
          "bg-accent text-white hover:bg-accent/90": variant === "primary",
          "bg-bg-surface border border-border-subtle text-text hover:border-accent": variant === "secondary",
          "text-text-muted hover:text-text hover:bg-bg-hover": variant === "ghost",
          "px-3 py-1.5 text-xs": size === "sm",
          "px-4 py-2 text-sm": size === "md",
        },
        className
      )}
      disabled={loading}
      {...props}
    >
      {loading && <Loader2 size={12} className="animate-spin" />}
      {children}
    </button>
  );
}

export default function SyncStatus() {
  const [status, setStatus] = useState<SyncStatusData | null>(null);
  const [jobs, setJobs] = useState<SyncJobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.get<SyncStatusData>("/api/v1/sync/status");
      setStatus(data);
    } catch {}
  }, []);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await api.get<SyncJobData[]>("/api/v1/sync/jobs");
      setJobs(data);
    } catch {}
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchJobs();
    const interval = setInterval(() => {
      fetchStatus();
      fetchJobs();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchJobs]);

  const handleStartSync = async (repoPath: string, embeddingModel: string, excludeDirs: string[]) => {
    setLoading(true);
    try {
      await syncApi.start(repoPath, embeddingModel, excludeDirs);
      await fetchStatus();
      await fetchJobs();
    } finally {
      setLoading(false);
    }
  };

  const handleStopSync = async (repoPath: string) => {
    try {
      await syncApi.stop(repoPath);
      await fetchStatus();
    } catch (err) {
      console.error("Failed to stop sync:", err);
    }
  };

  const handleDeletePath = async (repoPath: string) => {
    await handleStopSync(repoPath);
  };

  if (!status) return null;

  const activeJob = jobs.find(
    (j) => j.status === "pending" || j.status === "running"
  );

  const getStatusIcon = () => {
    if (activeJob || status.status === "indexing" || status.status === "syncing") {
      return <Loader2 size={12} className="animate-spin text-accent" />;
    }
    if (status.watching > 0) {
      return <Check size={12} className="text-success" />;
    }
    return <RefreshCw size={12} className="text-text-muted" />;
  };

  const getStatusText = () => {
    if (activeJob) {
      const progress = activeJob.progress || 0;
      const total = activeJob.total;
      if (total) {
        return `Indexing ${progress}/${total}...`;
      }
      return "Indexing...";
    }
    if (status.status === "indexing" || status.status === "syncing") {
      return `Syncing ${status.pending_changes} files...`;
    }
    if (status.watching > 0) {
      return `${status.watching} ${status.watching === 1 ? "path" : "paths"} watched`;
    }
    return "Not watching";
  };

  const getLastSyncText = () => {
    if (!status.last_sync) return null;
    const date = new Date(status.last_sync);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          {getStatusIcon()}
          <span>{getStatusText()}</span>
        </div>

        {status.last_sync && (
          <span className="text-[10px] text-text-muted/60">
            Last sync: {getLastSyncText()}
          </span>
        )}

        <button
          onClick={() => setSettingsOpen(true)}
          className="p-1 rounded hover:bg-bg-hover transition-colors"
          title="Sync settings"
        >
          <Settings size={12} className="text-text-muted" />
        </button>
      </div>

      <SyncSettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        onStartSync={handleStartSync}
        watchedPaths={status.watched_paths}
        onStopSync={handleStopSync}
        onDeletePath={handleDeletePath}
      />
    </>
  );
}

export { SyncStatus };
export type { SyncStatusData, SyncJobData, WatchedPath };
