"use client";

/**
 * DownloadProvider — unified download state + actions context.
 *
 * Single source of truth for all download state across the Models page.
 * Data sources:
 *   - WebSocket /ws/models — pushes active/queued state every 1s
 *   - REST GET /models/downloads/queue — initial load + fallback
 *   - REST GET /models/downloads/history — history drawer
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useWebSocket } from "@/shared/ws/useWebSocket";
import { downloads } from "@/features/integration/api";
import type { DownloadJob, DownloadHistoryItem } from "@/features/integration/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface DownloadState {
  active: DownloadJob[];
  queued: DownloadJob[];
  history: DownloadHistoryItem[];
  connected: boolean;
}

export interface DownloadActions {
  download: (modelId: string, variant?: string) => Promise<void>;
  pause: (jobId: string) => Promise<void>;
  resume: (jobId: string) => Promise<void>;
  cancel: (modelId: string) => Promise<void>;
  deleteLocal: (modelId: string) => Promise<void>;
  retry: (modelId: string) => Promise<void>;
  bulkCancel: (jobIds: string[]) => Promise<void>;
  clearCompleted: () => Promise<void>;
  refresh: () => Promise<void>;
}

interface DownloadContextType {
  state: DownloadState;
  actions: DownloadActions;
}

// ── Context ────────────────────────────────────────────────────────────────

const DownloadContext = createContext<DownloadContextType | null>(null);

export function useDownloadContext(): DownloadContextType {
  const ctx = useContext(DownloadContext);
  if (!ctx) throw new Error("useDownloadContext must be used within DownloadProvider");
  return ctx;
}

// ── Provider ───────────────────────────────────────────────────────────────

export function DownloadProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<DownloadJob[]>([]);
  const [queued, setQueued] = useState<DownloadJob[]>([]);
  const [history, setHistory] = useState<DownloadHistoryItem[]>([]);

  const activeRef = useRef(active);
  activeRef.current = active;

  // ── Load queue from REST (initial + fallback) ────────────────────────

  const loadQueue = useCallback(async () => {
    try {
      const res = await downloads.queue();
      setActive(res.active);
      setQueued(res.queued);
    } catch {
      // ignore — WS will catch up
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await downloads.history(30);
      setHistory(res.history);
    } catch {
      // ignore
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadQueue();
    loadHistory();
  }, [loadQueue, loadHistory]);

  // ── WebSocket for real-time progress ─────────────────────────────────

  const handleWSMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type !== "model_progress" || !Array.isArray(data.models)) return;

    const models = data.models as Array<{
      name: string;
      progress: number;
      status: string;
      speed_bytes_sec: number;
      eta_seconds: number | null;
      bytes_downloaded: number;
      total_bytes: number;
      queue_position: number | null;
      download_id: string;
      error?: string;
    }>;

    const newActive: DownloadJob[] = [];
    const newQueued: DownloadJob[] = [];
    const terminalStatuses = new Set(["completed", "failed", "cancelled"]);
    let hasTerminal = false;

    for (const m of models) {
      const job: DownloadJob = {
        job_id: m.download_id,
        model_id: m.name,
        status: m.status,
        progress: m.progress,
        speed_bytes_sec: m.speed_bytes_sec,
        downloaded_bytes: m.bytes_downloaded,
        total_bytes: m.total_bytes,
        eta_seconds: m.eta_seconds,
        queue_position: m.queue_position,
        error: m.error ?? null,
      };

      if (m.status === "downloading" || m.status === "paused") {
        newActive.push(job);
      } else if (m.status === "queued") {
        newQueued.push(job);
      }

      if (terminalStatuses.has(m.status)) {
        hasTerminal = true;
      }
    }

    setActive(newActive);
    setQueued(newQueued);

    if (hasTerminal) {
      loadHistory();
    }
  }, [loadHistory]);

  const { status: wsStatus } = useWebSocket({
    path: "/api/v1/ws/models",
    enabled: true,
    onMessage: handleWSMessage,
  });

  // ── Actions ──────────────────────────────────────────────────────────

  const download = useCallback(async (modelId: string, variant?: string) => {
    // Optimistically add to active
    const optimisticJob: DownloadJob = {
      job_id: `optimistic-${Date.now()}`,
      model_id: modelId,
      status: "downloading",
      progress: 0,
      speed_bytes_sec: null,
      downloaded_bytes: 0,
      total_bytes: 0,
      eta_seconds: null,
      queue_position: null,
      error: null,
    };
    setActive(prev => {
      if (prev.some(j => j.model_id === modelId)) return prev;
      return [...prev, optimisticJob];
    });

    try {
      await downloads.download(modelId, variant);
    } catch {
      setActive(prev => prev.filter(j => j.job_id !== optimisticJob.job_id));
    }
  }, []);

  const pause = useCallback(async (jobId: string) => {
    try {
      await downloads.pause(jobId);
      // Optimistic: mark as paused locally
      setActive(prev => prev.map(j =>
        j.job_id === jobId ? { ...j, status: "paused" } : j
      ));
    } catch {
      // ignore — WS will correct
    }
  }, []);

  const resume = useCallback(async (jobId: string) => {
    try {
      await downloads.resume(jobId);
      // Optimistic: mark as queued locally
      setActive(prev => prev.map(j =>
        j.job_id === jobId ? { ...j, status: "queued" } : j
      ));
    } catch {
      // ignore
    }
  }, []);

  const cancel = useCallback(async (modelId: string) => {
    try {
      await downloads.cancel(modelId);
    } catch {
      // ignore
    }
    // Remove from active and queued
    setActive(prev => prev.filter(j => j.model_id !== modelId));
    setQueued(prev => prev.filter(j => j.model_id !== modelId));
    // Refresh history
    setTimeout(() => loadHistory(), 500);
  }, [loadHistory]);

  const deleteLocal = useCallback(async (modelId: string) => {
    // Cancel if downloading/queued
    setActive(prev => prev.filter(j => j.model_id !== modelId));
    setQueued(prev => prev.filter(j => j.model_id !== modelId));

    try {
      await downloads.deleteLocal(modelId);
    } catch {
      // ignore
    }
    loadHistory();
  }, [loadHistory]);

  const retry = useCallback(async (modelId: string) => {
    try {
      await downloads.download(modelId);
      loadQueue();
    } catch {
      // ignore
    }
  }, [loadQueue]);

  const bulkCancel = useCallback(async (jobIds: string[]) => {
    try {
      await downloads.bulkCancel(jobIds);
    } catch {
      // ignore
    }
    setActive(prev => prev.filter(j => !jobIds.includes(j.job_id)));
    setQueued(prev => prev.filter(j => !jobIds.includes(j.job_id)));
    loadHistory();
  }, [loadHistory]);

  const clearCompleted = useCallback(async () => {
    try {
      await downloads.clearCompleted();
    } catch {
      // ignore
    }
    setHistory([]);
  }, []);

  const refresh = useCallback(async () => {
    await Promise.all([loadQueue(), loadHistory()]);
  }, [loadQueue, loadHistory]);

  // ── Value ────────────────────────────────────────────────────────────

  const state: DownloadState = useMemo(() => ({
    active,
    queued,
    history,
    connected: wsStatus === "connected",
  }), [active, queued, history, wsStatus]);

  const actions: DownloadActions = useMemo(() => ({
    download,
    pause,
    resume,
    cancel,
    deleteLocal,
    retry,
    bulkCancel,
    clearCompleted,
    refresh,
  }), [download, pause, resume, cancel, deleteLocal, retry, bulkCancel, clearCompleted, refresh]);

  const value: DownloadContextType = useMemo(() => ({
    state,
    actions,
  }), [state, actions]);

  return (
    <DownloadContext.Provider value={value}>
      {children}
    </DownloadContext.Provider>
  );
}
