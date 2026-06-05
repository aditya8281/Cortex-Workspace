"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner } from "@/components/ui/base";
import { healthService } from "@/services/api/admin";
import type { HealthStatus } from "@/types/api";

export default function HealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const data = await healthService.checkDeep();
        setHealth(data);
      } catch (err: any) {
        setError(err.message || "Failed to fetch health status");
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">System Health</h1>

      {error && <p className="text-danger">{error}</p>}

      {health && (
        <Card className="p-6 bg-slate-900/40 border-slate-800/80 rounded-2xl">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-900 pb-3">
              <span className="text-sm font-mono uppercase font-bold text-slate-300">Overall System Health</span>
              <Badge
                variant={health.status === "ready" || health.status === "healthy" ? "secondary" : "danger"}
              >
                {(health.status || "UNKNOWN").toUpperCase()}
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-3.5 bg-slate-950/40 border border-slate-900 rounded-xl">
                <span className="text-xs font-mono uppercase text-slate-400">Database Pool</span>
                <Badge variant={health.checks?.database ? "secondary" : "danger"}>
                  {health.checks?.database ? "OK" : "ERROR"}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3.5 bg-slate-950/40 border border-slate-900 rounded-xl">
                <span className="text-xs font-mono uppercase text-slate-400">Cognitive Memory</span>
                <Badge variant={health.checks?.memory ? "secondary" : "danger"}>
                  {health.checks?.memory ? "OK" : "ERROR"}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3.5 bg-slate-950/40 border border-slate-900 rounded-xl">
                <span className="text-xs font-mono uppercase text-slate-400">RAG Context Engine</span>
                <Badge variant={health.checks?.rag ? "secondary" : "danger"}>
                  {health.checks?.rag ? "OK" : "ERROR"}
                </Badge>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
