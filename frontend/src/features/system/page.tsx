"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { LogViewer } from "./components/LogViewer";
import { systemApi, type LLMHealth } from "./api";
import { useMetrics } from "@/shared/ws/MetricsProvider";

export default function SystemPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const { metrics, processes, logs, connected } = useMetrics();

  const [llm, setLlm] = useState<LLMHealth | null>(null);

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

  useEffect(() => {
    loadLLM();
    const interval = setInterval(loadLLM, 30000);
    return () => clearInterval(interval);
  }, [loadLLM]);

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
            <StatusDot color={connected ? "success" : "danger"} pulse={connected} />
            <span className="text-xs text-text-muted">{connected ? "Live" : "Offline"}</span>
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
              {llm?.installed_models?.map((m) => (
                <Badge key={m} variant={m === llm.active_model ? "success" : "default"}>
                  {m}
                </Badge>
              ))}
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

        {/* Logs — live from shared MetricsProvider */}
        <LogViewer logs={logs} />
      </div>
    </AppShell>
  );
}
