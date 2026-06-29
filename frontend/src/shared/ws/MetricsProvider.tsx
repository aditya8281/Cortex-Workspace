"use client";

/**
 * Global metrics WebSocket — single connection, shared across all pages.
 *
 * Backend pushes metrics every 500ms + logs every 3s + processes every 5s.
 * System page and dashboard both consume from here.
 *
 * Uses the shared useWebSocket hook so there's one WS connection pattern
 * across the entire app (no duplicate connection logic).
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useWebSocket } from "./useWebSocket";

// ── Types ──────────────────────────────────────────────────────────────────

/** Runtime type guard — validates incoming metrics payload at the boundary. */
function isLiveMetrics(data: unknown): data is LiveMetrics {
  if (typeof data !== "object" || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.cpu_percent === "number" &&
    typeof d.ram_percent === "number" &&
    typeof d.ram_used_gb === "number" &&
    typeof d.ram_total_gb === "number" &&
    typeof d.gpu_name === "string" &&
    typeof d.gpu_type === "string" &&
    (d.gpu_percent === null || typeof d.gpu_percent === "number") &&
    typeof d.disk_total_gb === "number" &&
    typeof d.disk_used_gb === "number" &&
    typeof d.disk_percent === "number"
  );
}

/** Runtime type guard for a single process info item. */
function isProcessInfo(item: unknown): item is ProcessInfo {
  if (typeof item !== "object" || item === null) return false;
  const o = item as Record<string, unknown>;
  return (
    typeof o.pid === "number" &&
    typeof o.name === "string" &&
    typeof o.cpu_percent === "number" &&
    typeof o.memory_percent === "number"
  );
}

/** Runtime type guard for a single system log item. */
function isSystemLog(item: unknown): item is SystemLog {
  if (typeof item !== "object" || item === null) return false;
  const o = item as Record<string, unknown>;
  return (
    typeof o.timestamp === "string" &&
    typeof o.level === "string" &&
    typeof o.module === "string" &&
    typeof o.message === "string"
  );
}

export interface LiveMetrics {
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  gpu_name: string;
  gpu_type: string;
  gpu_percent: number | null;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
}

export interface SystemLog {
  timestamp: string;
  level: string;
  module: string;
  message: string;
}

interface MetricsContextType {
  /** Latest system metrics (updates 2x/sec). null until first WS message. */
  metrics: LiveMetrics | null;
  /** Top processes (updates ~every 5s). */
  processes: ProcessInfo[];
  /** Recent logs (updates ~every 3s). */
  logs: SystemLog[];
  /** WS connection status. */
  connected: boolean;
}

const MetricsContext = createContext<MetricsContextType>({
  metrics: null,
  processes: [],
  logs: [],
  connected: false,
});

export function useMetrics() {
  return useContext(MetricsContext);
}

// ── Provider ───────────────────────────────────────────────────────────────

export function MetricsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [logs, setLogs] = useState<SystemLog[]>([]);

  const handleMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type === "metrics" && isLiveMetrics(data)) {
      setMetrics(data);
    } else if (data.type === "logs" && Array.isArray(data.logs) && data.logs.every(isSystemLog)) {
      setLogs(data.logs);
    } else if (data.type === "processes" && Array.isArray(data.processes) && data.processes.every(isProcessInfo)) {
      setProcesses(data.processes);
    }
  }, []);

  const { status } = useWebSocket({
    path: "/api/v1/ws/system",
    enabled: !!user,
    onMessage: handleMessage,
  });

  const value = useMemo<MetricsContextType>(
    () => ({
      metrics,
      processes,
      logs,
      connected: status === "connected",
    }),
    [metrics, processes, logs, status],
  );

  return (
    <MetricsContext.Provider value={value}>
      {children}
    </MetricsContext.Provider>
  );
}
