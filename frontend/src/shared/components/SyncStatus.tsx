"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Check, Loader2, Settings, X, ChevronDown } from "lucide-react";
import { api } from "@/shared/api/client";
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

const EMBEDDING_MODELS = [
  { value: "nomic-embed-text", label: "nomic-embed-text" },
  { value: "mxbai-embed-large", label: "mxbai-embed-large" },
  { value: "thenomic-embed-text-v1.5", label: "thenomic-embed-text-v1.5" },
  { value: "embed-models", label: "embed-models (all-in-one)" },
];

interface SyncSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStartSync: (repoPath: string, embeddingModel: string) => Promise<void>;
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
  const [repoPath, setRepoPath] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("nomic-embed-text");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath.trim()) return;
    setLoading(true);
    setError("");
    try {
      await onStartSync(repoPath.trim(), embeddingModel);
      setRepoPath("");
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start sync");
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-bg-elevated rounded-xl border border-border-subtle shadow-2xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-4 border-b border-border-subtle">
          <h2 className="text-sm font-semibold text-text">Auto-Sync Settings</h2>
          <button
            onClick={() => onOpenChange(false)}
            className="text-text-muted hover:text-text transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1.5">
                Directory Path
              </label>
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="/path/to/your/project"
                className="w-full px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
              />
            </div>

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
                  {EMBEDDING_MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={14}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
                />
              </div>
            </div>

            {error && (
              <p className="text-xs text-error">{error}</p>
            )}

            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={loading}
              className="w-full"
            >
              Start Sync
            </Button>
          </form>

          {watchedPaths.length > 0 && (
            <div className="pt-4 border-t border-border-subtle">
              <h3 className="text-xs font-medium text-text-muted mb-2">Watched Directories</h3>
              <div className="space-y-2">
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

  const handleStartSync = async (repoPath: string, embeddingModel: string) => {
    setLoading(true);
    try {
      await api.post("/api/v1/sync/start", {
        repo_path: repoPath,
        embedding_model: embeddingModel,
      });
      await fetchStatus();
      await fetchJobs();
    } finally {
      setLoading(false);
    }
  };

  const handleStopSync = async (repoPath: string) => {
    try {
      await api.post("/api/v1/sync/stop", { repo_path: repoPath });
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
      return `${status.watching} ${status.watching === 1 ? "repo" : "repos"} watched`;
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
export type { SyncStatusData, SyncJobData, WatchedPath, EMBEDDING_MODELS };