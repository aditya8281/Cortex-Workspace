"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { MetricsGrid } from "./components/MetricsGrid";
import { LogViewer } from "./components/LogViewer";
import { systemApi, type LLMHealth } from "./api";

export default function SystemPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [llm, setLlm] = useState<LLMHealth | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

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
        <div>
          <h1 className="text-headline font-semibold text-text-primary">System</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Health monitoring and diagnostics
          </p>
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

        {/* Metrics */}
        <div>
          <h2 className="text-title font-semibold text-text-primary mb-3">System Metrics</h2>
          <MetricsGrid
            metrics={{
              cpu_percent: 0,
              memory_percent: 0,
              disk_percent: 0,
              active_connections: 0,
              requests_today: 0,
              avg_response_ms: 0,
            }}
          />
        </div>

        {/* Logs */}
        <LogViewer logs={[]} />
      </div>
    </AppShell>
  );
}
