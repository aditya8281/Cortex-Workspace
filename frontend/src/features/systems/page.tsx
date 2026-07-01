"use client";

import { SystemsIcon } from "@/shared/ui/icons";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { LogViewer } from "@/features/system/components/LogViewer";
import { systemApi, type LLMHealth } from "@/features/system/api";
import type { SystemLog } from "@/features/system/components/LogViewer";
import { useMetrics } from "@/shared/ws/MetricsProvider";
import { Skeleton } from "@/shared/ui/Skeleton";

export default function SystemPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const { metrics, processes, logs, connected } = useMetrics();

  const [llm, setLlm] = useState<LLMHealth | null>(null);
  const [restLogs, setRestLogs] = useState<SystemLog[]>([]);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  // Load LLM health via REST (low frequency, not worth WS)
  const loadLLM = useCallback(async () => {
    try {
      const data = await systemApi.getLLMHealth();
      setLlm(data);
    } catch {
      // ignore
    }
  }, []);

  // REST fallback for logs — polls every 5s if WS not connected
  // WS pushes logs every ~3s, but may not be connected or may miss initial data
  const loadLogs = useCallback(async () => {
    try {
      const data = await systemApi.getLogs(50);
      if (data?.logs) setRestLogs(data.logs as SystemLog[]);
    } catch {
      // ignore — WS will provide logs when connected
    }
  }, []);

  useEffect(() => {
    loadLLM();
    loadLogs();
    const llmInterval = setInterval(loadLLM, 30000);
    const logsInterval = setInterval(loadLogs, 5000);
    return () => { clearInterval(llmInterval); clearInterval(logsInterval); };
  }, [loadLLM, loadLogs]);

  if (loading || !user) return (
    <div className="h-full overflow-y-auto p-6">
      <div className="space-y-6">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-4 w-40" />
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <Skeleton className="h-3 w-3 rounded-full" />
            <div className="space-y-1">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-3 w-48" />
            </div>
          </div>
        </Card>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-4">
              <Skeleton className="h-3 w-12 mb-2" />
              <Skeleton className="h-6 w-20 mb-3" />
              <Skeleton className="h-1.5 w-full rounded-full" />
            </Card>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">System</h1>

            <p className="mt-1 text-sm text-text-secondary">
              Health monitoring and diagnostics
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot color={connected ? "success" : "danger"} pulse={connected} />
            <span className="text-xs text-text-muted">{connected ? "Live" : "Offline"}</span>
          </div>
        </div>

        {/* LLM Status */}
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusDot
                color={llm?.status === "healthy" ? "success" : llm?.status === "error" ? "danger" : "warning"}
                pulse={llm?.status === "healthy"}
              />
              <div>
                <p className="text-sm font-medium text-text-primary">LLM Engine</p>
                <p className="text-xs text-text-muted">
                  {llm?.status ?? "unknown"} {llm?.latency_ms != null ? `· ${Math.round(llm.latency_ms)}ms` : ""}
                  {llm?.error && <span className="text-danger ml-1">· {llm.error}</span>}
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Metrics — live from shared MetricsProvider (2/sec) */}
        <div>
          <h2 className="text-title font-semibold text-text-primary mb-3">System Metrics</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "CPU", value: `${(metrics?.cpu_percent ?? 0).toFixed(1)}%`, percent: metrics?.cpu_percent ?? 0 },
              { label: "RAM", value: `${(metrics?.ram_used_gb ?? 0).toFixed(1)} / ${(metrics?.ram_total_gb ?? 0).toFixed(0)} GB`, percent: metrics?.ram_percent ?? 0 },
              { label: "GPU", value: metrics?.gpu_name && metrics.gpu_name !== "No GPU detected" ? `${(metrics?.gpu_percent ?? 0).toFixed(1)}%` : "N/A", percent: metrics?.gpu_percent ?? 0 },
              { label: "Disk", value: `${(metrics?.disk_used_gb ?? 0).toFixed(0)} / ${(metrics?.disk_total_gb ?? 0).toFixed(0)} GB`, percent: metrics?.disk_percent ?? 0 },
            ].map(({ label, value, percent }) => (
              <Card key={label} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-text-muted font-medium">{label}</p>
                  <p className="text-xs text-text-muted">{percent.toFixed(1)}%</p>
                </div>
                <p className="text-lg font-semibold text-text-primary tabular-nums mb-3">{value}</p>
                <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-[width] duration-300 ease-out ${
                      percent < 70 ? "bg-success" : percent < 85 ? "bg-warning" : "bg-danger"
                    }`}
                    style={{ width: `${Math.min(percent, 100)}%` }}
                  />
                </div>
              </Card>
            ))}
          </div>
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

        {/* Top Processes — live from shared MetricsProvider */}
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

        {/* Logs — live from WS + REST fallback */}
        <LogViewer logs={connected ? logs : restLogs} />
      </div>
    </div>
  );
}
