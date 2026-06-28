"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { MetricsGrid } from "./components/MetricsGrid";
import { LogViewer } from "./components/LogViewer";
import { systemApi, type LLMHealth, type SystemLog } from "./api";
import { useWebSocket, type WSStatus } from "@/shared/ws/useWebSocket";

interface SystemMetrics {
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

interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
}

export default function SystemPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [llm, setLlm] = useState<LLMHealth | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const logsRef = useRef<SystemLog[]>([]);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  // Load LLM health via REST (not real-time enough for WS)
  const loadLLM = useCallback(async () => {
    try {
      const data = await systemApi.getLLMHealth();
      setLlm(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadLLM();
    const interval = setInterval(loadLLM, 30000);
    return () => clearInterval(interval);
  }, [loadLLM]);

  // WebSocket for real-time metrics and logs
  const handleWSMessage = useCallback((data: Record<string, unknown>) => {
    const type = data.type as string;

    if (type === "metrics") {
      setMetrics(data as unknown as SystemMetrics);
    } else if (type === "logs") {
      const incoming = data.logs as SystemLog[];
      if (Array.isArray(incoming)) {
        logsRef.current = incoming;
        setLogs([...incoming]);
      }
    } else if (type === "processes") {
      setProcesses(data.processes as ProcessInfo[]);
    }
  }, []);

  const { status: wsStatus } = useWebSocket({
    path: "/api/v1/ws/system",
    enabled: !!user,
    onMessage: handleWSMessage,
  });

  const wsStatusText: Record<WSStatus, string> = {
    connecting: "Connecting…",
    connected: "Live",
    disconnected: "Offline",
    error: "Error",
  };

  const wsStatusColor: Record<WSStatus, "success" | "warning" | "danger"> = {
    connecting: "warning",
    connected: "success",
    disconnected: "danger",
    error: "danger",
  };

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">System</h1>
            <p className="mt-1 text-sm text-text-secondary">
              Health monitoring and diagnostics
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot color={wsStatusColor[wsStatus]} pulse={wsStatus === "connected"} />
            <span className="text-xs text-text-muted">{wsStatusText[wsStatus]}</span>
          </div>
        </div>

        {/* LLM Status */}
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusDot
                color={llm?.ollama === "healthy" ? "success" : llm?.ollama === "degraded" ? "warning" : "danger"}
                pulse={llm?.ollama === "healthy"}
              />
              <div>
                <p className="text-sm font-medium text-text-primary">LLM Engine</p>
                <p className="text-xs text-text-muted">
                  {llm?.active_model ?? "No model loaded"} · {llm?.ollama ?? "unknown"}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              {llm?.installed_models.map((m) => (
                <Badge key={m} variant={m === llm.active_model ? "success" : "default"}>
                  {m}
                </Badge>
              ))}
            </div>
          </div>
        </Card>

        {/* Metrics — live from WebSocket */}
        <div>
          <h2 className="text-title font-semibold text-text-primary mb-3">System Metrics</h2>
          <MetricsGrid
            metrics={{
              cpu_percent: metrics?.cpu_percent ?? 0,
              memory_percent: metrics?.ram_percent ?? 0,
              gpu_percent: metrics?.gpu_percent ?? 0,
              disk_percent: metrics?.disk_percent ?? 0,
              ram_used_gb: metrics?.ram_used_gb ?? 0,
              ram_total_gb: metrics?.ram_total_gb ?? 0,
              gpu_name: metrics?.gpu_name ?? "",
            }}
          />
        </div>

        {/* GPU Info — shown when GPU detected */}
        {metrics?.gpu_name && metrics.gpu_name !== "No GPU detected" && (
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">{metrics.gpu_name}</p>
                <p className="text-xs text-text-muted">{metrics.gpu_type}</p>
              </div>
              {metrics.gpu_percent != null && (
                <div className="text-right">
                  <span className="text-headline font-semibold tabular-nums text-text-primary">
                    {Math.round(metrics.gpu_percent)}
                  </span>
                  <span className="text-xs text-text-muted ml-1">%</span>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Top Processes */}
        {processes.length > 0 && (
          <Card className="overflow-hidden">
            <div className="px-4 py-3 border-b border-border-subtle">
              <h3 className="text-sm font-medium text-text-primary">Top Processes</h3>
            </div>
            <div className="max-h-60 overflow-y-auto">
              {processes.map((proc) => (
                <div
                  key={proc.pid}
                  className="flex items-center gap-4 px-4 py-2 border-b border-border-subtle last:border-0"
                >
                  <span className="text-xs text-text-muted w-16 tabular-nums">PID {proc.pid}</span>
                  <span className="text-sm text-text-primary flex-1 truncate">{proc.name}</span>
                  <span className="text-xs tabular-nums text-text-secondary">{proc.cpu_percent}%</span>
                  <span className="text-xs tabular-nums text-text-muted">{proc.memory_percent}%</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Logs — live from WebSocket */}
        <LogViewer logs={logs} />
      </div>
    </AppShell>
  );
}
