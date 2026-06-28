"use client";

/**
 * Global metrics WebSocket — single connection, shared across all pages.
 *
 * Backend pushes metrics every 500ms + logs every 3s + processes every 5s.
 * System page and dashboard both consume from here.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "@/shared/auth/AuthProvider";

// ── Types ──────────────────────────────────────────────────────────────────

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

// ── WebSocket URL ──────────────────────────────────────────────────────────

function getWsBaseUrl(): string {
  if (typeof window === "undefined") return "ws://localhost:8000";
  return `ws://${window.location.hostname}:8000`;
}

// ── Provider ───────────────────────────────────────────────────────────────

export function MetricsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(async () => {
    if (!user || !mountedRef.current) return;
    cleanup();
    setConnected(false);

    try {
      const res = await fetch("/api/v1/auth/ws-token", { credentials: "include" });
      if (!res.ok) return;
      const { token } = await res.json();

      const url = `${getWsBaseUrl()}/api/v1/ws/system?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (mountedRef.current) {
          setConnected(true);
          retryRef.current = 0;
        }
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === "metrics") {
            setMetrics(data);
          } else if (data.type === "logs" && Array.isArray(data.logs)) {
            setLogs(data.logs);
          } else if (data.type === "processes" && Array.isArray(data.processes)) {
            setProcesses(data.processes);
          }
        } catch { /* non-JSON */ }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnected(false);
        // Reconnect with backoff
        const delay = [1000, 2000, 4000, 8000, 16000][Math.min(retryRef.current, 4)];
        retryRef.current += 1;
        timerRef.current = setTimeout(() => { if (mountedRef.current) connect(); }, delay);
      };

      ws.onerror = () => {};
    } catch {
      // retry
      if (mountedRef.current) {
        const delay = [1000, 2000, 4000][Math.min(retryRef.current, 2)];
        retryRef.current += 1;
        timerRef.current = setTimeout(() => connect(), delay);
      }
    }
  }, [user, cleanup]);

  useEffect(() => {
    mountedRef.current = true;
    if (user) connect();
    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [user, connect, cleanup]);

  return (
    <MetricsContext.Provider value={{ metrics, processes, logs, connected }}>
      {children}
    </MetricsContext.Provider>
  );
}
