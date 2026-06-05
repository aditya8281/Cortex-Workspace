"use client";

import { useState, useEffect, useRef } from "react";
import { Button, Card, Badge } from "@/components/ui/base";
import { syncService } from "@/services/api/sync";
import type { WorkspaceIntelligence } from "@/types/api";
import { 
  RefreshCw, CheckCircle, Clock, Folder, Play, StopCircle, 
  AlertTriangle, ArrowUpRight, ShieldCheck, Database, HardDrive, Terminal
} from "lucide-react";
import { apiClient } from "@/services/api/client";
import { useIsMounted } from "@/hooks/useIsMounted";
import { API_ENDPOINTS } from "@/constants/endpoints";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

export default function SyncPage() {
  const [intelligence, setIntelligence] = useState<WorkspaceIntelligence | null>(null);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const mountedRef = useIsMounted();

  const fetchData = async () => {
    try {
      const [intData, statusData] = await Promise.all([
        syncService.getIntelligence(),
        syncService.getStatus(),
      ]);
      if (mountedRef.current) {
        setIntelligence(intData);
        setSyncStatus(statusData);
      }
    } catch (error) {
      console.error("Failed to fetch sync data:", error);
    }
  };

  useEffect(() => {
    const initFetch = async () => {
      setLoading(true);
      await fetchData();
      if (mountedRef.current) setLoading(false);
    };
    initFetch();
  }, []);

  // Poll sync status when active sync is running
  useEffect(() => {
    const isSyncActive = syncStatus?.sync_status === "syncing" || 
                         syncStatus?.active_sync_status === "syncing";

    if (isSyncActive) {
      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(async () => {
          await fetchData();
        }, 3000);
      }
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [syncStatus]);

  const handleTriggerSync = async () => {
    try {
      setActionLoading(true);
      await apiClient.postSafe(API_ENDPOINTS.SYNC_NOW);
      await fetchData();
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      if (mountedRef.current) setActionLoading(false);
    }
  };

  const handleForceResync = async () => {
    try {
      setActionLoading(true);
      await apiClient.postSafe(API_ENDPOINTS.SYNC_FORCE);
      await fetchData();
    } catch (error) {
      console.error("Force resync failed:", error);
    } finally {
      if (mountedRef.current) setActionLoading(false);
    }
  };

  const handleCancelSync = async () => {
    try {
      setActionLoading(true);
      await apiClient.postSafe(API_ENDPOINTS.SYNC_CANCEL);
      await fetchData();
    } catch (error) {
      console.error("Cancel sync failed:", error);
    } finally {
      if (mountedRef.current) setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <ErrorBoundary>
        <div className="flex items-center justify-center min-h-[calc(100vh-6rem)]">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Loading telemetry...</span>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  const isSyncing = syncStatus?.sync_status === "syncing" || syncStatus?.active_sync_status === "syncing";

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800/60 pb-4 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono">Workspace Sync Center</h1>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Monitor and run semantic index and neural knowledge syncs on your codebase workspace.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isSyncing ? (
            <button
              onClick={handleCancelSync}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 bg-red-950/40 border border-red-900/30 text-red-400 text-xs font-semibold rounded-xl hover:bg-red-900/20 active:translate-y-[1px] transition-all disabled:opacity-50"
            >
              <StopCircle size={14} />
              Abort Sync
            </button>
          ) : (
            <>
              <button
                onClick={handleTriggerSync}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-xl active:translate-y-[1px] transition-all shadow-[0_4px_12px_rgba(6,182,212,0.15)] disabled:opacity-50"
              >
                <Play size={14} className="fill-current" />
                Index Sync
              </button>
              <button
                onClick={handleForceResync}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-semibold rounded-xl active:translate-y-[1px] transition-all disabled:opacity-50"
              >
                <RefreshCw size={14} />
                Force Re-build
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Status Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Sync Wheel Card */}
        <Card className="bg-slate-900/40 border-slate-800/80 p-6 flex flex-col items-center justify-center text-center relative overflow-hidden rounded-2xl md:col-span-1 min-h-[220px]">
          <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-slate-500">TELEM_MODULE</div>
          
          <div className="relative flex items-center justify-center mb-4">
            <div className={`w-28 h-28 rounded-full border-2 ${isSyncing ? "border-cyan-500/10 border-t-cyan-500 animate-spin" : "border-slate-800"} flex items-center justify-center transition-all duration-300`} style={{ animationDuration: '3s' }}>
              <div className={`w-24 h-24 rounded-full border border-dashed ${isSyncing ? "border-cyan-500/20 border-r-cyan-500 animate-spin" : "border-slate-800/40"} flex items-center justify-center`} style={{ animationDuration: '10s' }}>
                <div className="w-20 h-20 bg-slate-950/80 rounded-full flex flex-col items-center justify-center border border-slate-800/50">
                  <Database className={`w-6 h-6 ${isSyncing ? "text-cyan-400 animate-pulse" : "text-slate-400"}`} />
                  <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mt-1.5">
                    {syncStatus?.sync_status || "IDLE"}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <h3 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wide">
            {isSyncing ? "Synchronizing Index" : "Database Synchronized"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-1">
            {isSyncing ? syncStatus?.progress_message || "Processing filesystem changes..." : "All workspace indexes up to date."}
          </p>
        </Card>

        {/* Sync Telemetry Dashboard */}
        <Card className="bg-slate-900/40 border-slate-800/80 p-6 rounded-2xl md:col-span-2 space-y-5 relative">
          <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-slate-500">LIVE_METRICS</div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Indexed Files</span>
              <div className="text-2xl font-bold font-mono text-white">
                {intelligence?.indexed_files || syncStatus?.indexed || 0}
              </div>
            </div>
            
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Total Tracked</span>
              <div className="text-2xl font-bold font-mono text-white">
                {intelligence?.total_files || syncStatus?.tracked_files || 0}
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Index Status</span>
              <div>
                <Badge variant={isSyncing ? "secondary" : "primary"}>
                  {intelligence?.status || syncStatus?.sync_status || "idle"}
                </Badge>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Memory Updates</span>
              <div className="text-2xl font-bold font-mono text-white">
                {syncStatus?.memory_updates || 0}
              </div>
            </div>
          </div>

          {/* Sync Progress Bar */}
          {isSyncing && (
            <div className="space-y-2 pt-2 border-t border-slate-900">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-cyan-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                  SYNCING: {syncStatus?.current_path ? `...${syncStatus.current_path.slice(-30)}` : "Analyzing files..."}
                </span>
                <span className="text-slate-300 font-bold">{Number(syncStatus?.progress_percent ?? 0).toFixed(1)}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 shadow-[0_0_10px_rgba(6,182,212,0.4)] transition-all duration-300"
                  style={{ width: `${syncStatus?.progress_percent || 0}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>Speed: {Number(syncStatus?.speed_files_per_sec ?? 0).toFixed(1)} files/s</span>
                <span>Est. time: {Number(syncStatus?.estimated_time_remaining ?? 0).toFixed(0)}s remaining</span>
              </div>
            </div>
          )}

          {!isSyncing && (
            <div className="flex items-center gap-2 pt-3 border-t border-slate-900 text-xs text-slate-400">
              <Clock size={14} className="text-slate-500" />
              <span>Last synchronized time: </span>
              <span className="font-mono text-slate-300">
                {syncStatus?.last_sync_time ? new Date(syncStatus.last_sync_time).toLocaleString() : "Never"}
              </span>
            </div>
          )}
        </Card>
      </div>

      {/* Discovery Roots / Watcher configuration */}
      <Card className="bg-slate-900/40 border-slate-800/80 p-6 rounded-2xl relative">
        <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-slate-500">SCOPE_CONFIG</div>
        
        <div className="flex items-center gap-2 mb-4 border-b border-slate-900 pb-3">
          <Folder className="w-4 h-4 text-cyan-400" />
          <h3 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wide">Tracked Discovery Roots</h3>
        </div>

        {syncStatus?.discovery_roots?.length === 0 ? (
          <p className="text-xs text-slate-500">No workspace paths actively tracked.</p>
        ) : (
          <div className="space-y-2">
            {syncStatus?.discovery_roots?.map((root: string, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-950/50 border border-slate-900 rounded-xl hover:border-slate-800 transition-colors">
                <div className="flex items-center gap-2.5 min-w-0">
                  <HardDrive size={14} className="text-slate-500 shrink-0" />
                  <span className="text-xs text-slate-300 font-mono truncate">{root}</span>
                </div>
                
                <span className="text-[9px] font-mono text-cyan-500/80 bg-cyan-950/20 border border-cyan-900/30 px-2 py-0.5 rounded-full shrink-0">
                  ACTIVE_WATCH
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
      
      {/* Real-time system log feed */}
      {isSyncing && (
        <Card className="bg-slate-950/90 border-slate-800 p-4 rounded-xl space-y-2.5 shadow-inner">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Terminal size={14} className="text-cyan-400 animate-pulse" />
            <span>FS_INDEXER_FEED // EVENT_STREAM</span>
          </div>
          
          <div className="font-mono text-[10px] space-y-1 text-slate-400 max-h-24 overflow-y-auto leading-normal">
            <div>&gt; [SYSTEM] Initializing parallel chunk extraction parser...</div>
            <div>&gt; [PARSER] Loading AST models for Python, TSX, Javascript</div>
            {syncStatus?.current_path && (
              <div className="text-cyan-400 animate-pulse">&gt; [PARSING] {syncStatus.current_path}</div>
            )}
            {syncStatus?.errors > 0 && (
              <div className="text-red-400">&gt; [WARNING] Failed to parse {syncStatus.errors} files. See logs.</div>
            )}
          </div>
        </Card>
      )}
      </div>
    </ErrorBoundary>
  );
}
