import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  useSyncStatus,
  useLatestSyncRun,
  useTriggerSync,
  useScopeConfig,
  useAddIncludeFolder,
  useAddExcludeFolder,
  useRemoveIncludeFolder,
  useRemoveExcludeFolder,
  usePauseSync,
  useResumeSync,
  useCancelSync,
  useForceResync,
} from "@/hooks/useIntelligence";
import { formatTimestamp } from "@/lib/utils";
import {
  RefreshCw,
  Square,
  Pause,
  Play,
  FolderPlus,
  AlertTriangle,
  Folder,
  XCircle,
  Activity,
  Gauge
} from "lucide-react";

export function SyncPage() {
  const { data: status, refetch: refetchStatus } = useSyncStatus();
  const { data: run, refetch: refetchRun } = useLatestSyncRun();
  const { data: config, refetch: refetchConfig } = useScopeConfig();

  const syncMutation = useTriggerSync();
  const forceResyncMutation = useForceResync();
  const pauseMutation = usePauseSync();
  const resumeMutation = useResumeSync();
  const cancelMutation = useCancelSync();
  const addInclude = useAddIncludeFolder();
  const addExclude = useAddExcludeFolder();
  const removeInclude = useRemoveIncludeFolder();
  const removeExclude = useRemoveExcludeFolder();

  const [includePath, setIncludePath] = useState("");
  const [excludePath, setExcludePath] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  // Sync is running if state status is syncing/paused, or DB status is running, or trigger pending
  const isRunning =
    status?.sync_status === "syncing" ||
    status?.sync_status === "paused" ||
    run?.status === "running" ||
    syncMutation.isPending ||
    forceResyncMutation.isPending;

  const isPaused = status?.sync_status === "paused";

  useEffect(() => {
    if (!isRunning) return;
    const id = window.setInterval(() => {
      void refetchStatus();
      void refetchRun();
    }, 1500);
    return () => window.clearInterval(id);
  }, [isRunning, refetchStatus, refetchRun]);

  useEffect(() => {
    if (run?.progress_message) {
      setLogs((prev) => {
        const next = [...prev, `${new Date().toLocaleTimeString()} — ${run.progress_message}`];
        return next.slice(-20);
      });
    }
    if (run?.result_summary) {
      setLogs((prev) => [...prev, `${new Date().toLocaleTimeString()} — ${run.result_summary}`].slice(-20));
    }
  }, [run?.progress_message, run?.result_summary]);

  const progress = isRunning ? (status?.progress_percent ?? 30) : run?.status === "completed" ? 100 : 0;

  const formatTimeRemaining = (seconds?: number) => {
    if (!seconds || seconds <= 0) return "Estimating...";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
  };

  const handleAddInclude = (e: React.FormEvent) => {
    e.preventDefault();
    if (!includePath.trim()) return;
    addInclude.mutate(includePath.trim(), {
      onSuccess: () => {
        setIncludePath("");
        void refetchConfig();
        void refetchStatus();
      }
    });
  };

  const handleAddExclude = (e: React.FormEvent) => {
    e.preventDefault();
    if (!excludePath.trim()) return;
    addExclude.mutate(excludePath.trim(), {
      onSuccess: () => {
        setExcludePath("");
        void refetchConfig();
        void refetchStatus();
      }
    });
  };

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8 bg-cortex-bg/30">
      <div className="mx-auto max-w-4xl space-y-6">
        
        {/* Header Section */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-cortex-border pb-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-cortex-primary via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Memory Sync Center
            </h2>
            <p className="text-sm text-cortex-muted">
              Configure, monitor, and synchronize Cortex's OS-wide filesystem knowledge base.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {!isRunning ? (
              <>
                <Button onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
                  <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                  Sync Now
                </Button>
                <Button variant="secondary" onClick={() => forceResyncMutation.mutate()} disabled={forceResyncMutation.isPending}>
                  <Gauge className="mr-2 h-4 w-4 text-amber-400" />
                  Force Resync
                </Button>
              </>
            ) : (
              <>
                {isPaused ? (
                  <Button variant="secondary" className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10" onClick={() => resumeMutation.mutate()}>
                    <Play className="mr-2 h-4 w-4" />
                    Resume
                  </Button>
                ) : (
                  <Button variant="secondary" className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10" onClick={() => pauseMutation.mutate()}>
                    <Pause className="mr-2 h-4 w-4" />
                    Pause
                  </Button>
                )}
                <Button variant="destructive" onClick={() => cancelMutation.mutate()}>
                  <Square className="mr-2 h-4 w-4" />
                  Stop Sync
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Current Live Status Card */}
        <Card className="border border-cortex-border bg-cortex-card/50 backdrop-blur-md">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Activity className={`h-4 w-4 ${isRunning && !isPaused ? "text-emerald-400 animate-pulse" : "text-cortex-muted"}`} />
                Current Status
              </CardTitle>
              <Badge variant={isRunning ? (isPaused ? "warn" : "success") : "default"}>
                {isRunning ? (isPaused ? "PAUSED" : "INDEXING") : "IDLE"}
              </Badge>
            </div>
            <CardDescription className="font-mono text-xs truncate max-w-full text-indigo-300">
              {isRunning
                ? (status?.current_path || "Scanning directories...")
                : (run?.result_summary ?? status?.progress_message ?? "Idle — awaiting synchronization request")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={progress} label="Sync progress" className="h-2.5" />
            
            {isRunning && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 text-xs">
                <div className="p-3 bg-cortex-bg/40 rounded-lg border border-cortex-border">
                  <span className="text-cortex-muted block mb-1">Discovered Files</span>
                  <span className="text-lg font-bold tabular-nums">{status?.total_files ?? 0}</span>
                </div>
                <div className="p-3 bg-cortex-bg/40 rounded-lg border border-cortex-border">
                  <span className="text-cortex-muted block mb-1">Indexed</span>
                  <span className="text-lg font-bold tabular-nums text-emerald-400">{status?.indexed ?? 0}</span>
                </div>
                <div className="p-3 bg-cortex-bg/40 rounded-lg border border-cortex-border">
                  <span className="text-cortex-muted block mb-1">Processing Speed</span>
                  <span className="text-lg font-bold tabular-nums text-indigo-300">{status?.speed_files_per_sec ?? 0} files/s</span>
                </div>
                <div className="p-3 bg-cortex-bg/40 rounded-lg border border-cortex-border">
                  <span className="text-cortex-muted block mb-1">Time Remaining</span>
                  <span className="text-lg font-bold tabular-nums text-purple-400">{formatTimeRemaining(status?.estimated_time_remaining)}</span>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 text-xs">
              <Badge>Last Sync: {formatTimestamp(status?.last_sync_time)}</Badge>
              <Badge>Sync Health: {status?.errors && status.errors > 0 ? "Degraded" : "Healthy"}</Badge>
              {status?.errors && status.errors > 0 ? (
                <Badge className="border-red-500/30 text-red-400 bg-red-500/5">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {status.errors} indexing errors
                </Badge>
              ) : null}
            </div>
          </CardContent>
        </Card>

        {/* Memory Scope Settings */}
        <Card className="border border-cortex-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Folder className="h-4 w-4 text-cortex-primary" />
              Memory Scope Configuration
            </CardTitle>
            <CardDescription>
              Specify which paths are recursively indexed (Include) or ignored (Exclude).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            
            {/* Include List */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold flex items-center justify-between">
                <span>INCLUDED DIRECTORIES (Indexed recursively)</span>
                <span className="text-xs font-normal text-cortex-muted">{config?.include_folders.length ?? 0} configured</span>
              </h4>
              <div className="flex flex-wrap gap-2 p-3 bg-cortex-bg/30 rounded-lg border border-cortex-border min-h-12 items-center">
                {config?.include_folders.map((path) => (
                  <Badge key={path} className="pl-3 pr-1 py-1 flex items-center gap-1 border border-indigo-500/25">
                    <span className="truncate max-w-xs">{path}</span>
                    <button
                      type="button"
                      onClick={() => removeInclude.mutate(path, { onSuccess: () => { void refetchConfig(); void refetchStatus(); } })}
                      className="text-cortex-muted hover:text-red-400 transition"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                    </button>
                  </Badge>
                ))}
                {config?.include_folders.length === 0 && <span className="text-xs text-cortex-muted italic">No custom directories included. Default folders will be scanned.</span>}
              </div>
              <form onSubmit={handleAddInclude} className="flex gap-2">
                <Input
                  placeholder="e.g. /home/user/my-codebase"
                  value={includePath}
                  onChange={(e) => setIncludePath(e.target.value)}
                  className="bg-cortex-bg/40 text-xs h-9 border-cortex-border"
                />
                <Button type="submit" size="sm" variant="secondary" className="h-9 px-3">
                  <FolderPlus className="h-4 w-4 mr-1" /> Add
                </Button>
              </form>
            </div>

            {/* Exclude List */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold flex items-center justify-between">
                <span>EXCLUDED PATHS (Always skipped)</span>
                <span className="text-xs font-normal text-cortex-muted">{config?.exclude_folders.length ?? 0} configured</span>
              </h4>
              <div className="flex flex-wrap gap-2 p-3 bg-cortex-bg/30 rounded-lg border border-cortex-border min-h-12 items-center">
                {config?.exclude_folders.map((path) => (
                  <Badge key={path} className="pl-3 pr-1 py-1 flex items-center gap-1 border border-red-500/10 text-cortex-muted">
                    <span className="truncate max-w-xs">{path}</span>
                    <button
                      type="button"
                      onClick={() => removeExclude.mutate(path, { onSuccess: () => { void refetchConfig(); void refetchStatus(); } })}
                      className="text-cortex-muted hover:text-red-400 transition"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                    </button>
                  </Badge>
                ))}
              </div>
              <form onSubmit={handleAddExclude} className="flex gap-2">
                <Input
                  placeholder="e.g. /home/user/archives"
                  value={excludePath}
                  onChange={(e) => setExcludePath(e.target.value)}
                  className="bg-cortex-bg/40 text-xs h-9 border-cortex-border"
                />
                <Button type="submit" size="sm" variant="secondary" className="h-9 px-3">
                  <FolderPlus className="h-4 w-4 mr-1" /> Add
                </Button>
              </form>
            </div>

          </CardContent>
        </Card>

        {/* Live Errors Console */}
        {status?.error_logs && status.error_logs.length > 0 && (
          <Card className="border border-red-500/20 bg-red-500/5">
            <CardHeader className="py-3">
              <CardTitle className="text-xs font-semibold text-red-400 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                INDEXING EXCEPTION CONSOLE
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-32 overflow-y-auto font-mono text-[10px] text-red-300 space-y-1 bg-black/30 p-2.5 rounded border border-red-500/10">
                {status.error_logs.map((err, i) => (
                  <p key={i}>⚠️ {err}</p>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Live Logs console */}
        <Card className="border border-cortex-border">
          <CardHeader>
            <CardTitle className="text-base">Sync Event logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-48 overflow-y-auto rounded-lg bg-cortex-bg/60 p-3.5 font-mono text-xs text-cortex-muted border border-cortex-border">
              {logs.length === 0 && <p className="italic text-cortex-muted/65">Waiting for sync activity logs...</p>}
              {logs.map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
