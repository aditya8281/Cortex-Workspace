"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { StatusDot } from "@/shared/ui/StatusDot";
import { dashboardApi, type LLMMetricsResponse, type LLMHealthResponse } from "../api";

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

function statusColor(status: string): "success" | "warning" | "danger" {
  if (status === "healthy") return "success";
  if (status === "degraded") return "warning";
  return "danger";
}

function formatLatency(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

// ── Skeleton ────────────────────────────────────────────────────────────────

function SkeletonGrid() {
  return (
    <div className="space-y-3">
      <Card className="p-5">
        <Skeleton className="h-3 w-20 mb-3" />
        <Skeleton className="h-8 w-24" />
      </Card>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[...Array(2)].map((_, i) => (
          <Card key={i} className="p-4">
            <Skeleton className="h-3 w-16 mb-3" />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Skeleton className="h-2 w-12 mb-1.5" />
                <Skeleton className="h-5 w-16" />
              </div>
              <div>
                <Skeleton className="h-2 w-12 mb-1.5" />
                <Skeleton className="h-5 w-16" />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ── Component ───────────────────────────────────────────────────────────────

export function MetricsRow() {
  const [llmMetrics, setLlmMetrics] = useState<LLMMetricsResponse | null>(null);
  const [llmHealth, setLlmHealth] = useState<LLMHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchData = () => {
      void Promise.all([
        dashboardApi.getLLMMetrics(),
        dashboardApi.getLLMHealth(),
      ])
        .then(([metrics, health]) => {
          if (!cancelled) {
            setLlmMetrics(metrics);
            setLlmHealth(health);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setLlmMetrics(null);
            setLlmHealth(null);
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) return <SkeletonGrid />;

  const healthStatus = llmHealth?.status ?? "unknown";
  const healthColor = statusColor(healthStatus);

  return (
    <div className="space-y-3">
      {/* Status — prominent full-width card */}
      <Card className="p-5">
        <p className="text-xs text-text-muted font-medium uppercase tracking-wider mb-3">
          LLM Status
        </p>
        <div className="flex items-center gap-3">
          <StatusDot
            color={healthColor}
            size="lg"
            pulse={healthStatus === "healthy"}
          />
          <div>
            <p className="text-lg font-semibold text-text-primary capitalize">
              {healthStatus}
            </p>
            {llmHealth && (
              <p className="text-xs text-text-muted">
                Latency: {formatLatency(llmHealth.latency_ms)}
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* Volume + Performance — two distinct cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Card className="p-4">
          <p className="text-xs text-text-muted font-medium uppercase tracking-wider mb-3">
            Volume
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[0.625rem] text-text-muted uppercase tracking-wider mb-1">
                Requests
              </p>
              <p className="text-xl font-semibold text-text-primary tabular-nums">
                {llmMetrics ? formatCount(llmMetrics.total_requests) : "—"}
              </p>
            </div>
            <div>
              <p className="text-[0.625rem] text-text-muted uppercase tracking-wider mb-1">
                Tokens
              </p>
              <p className="text-xl font-semibold text-text-primary tabular-nums">
                {llmMetrics ? formatCount(llmMetrics.total_tokens) : "—"}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <p className="text-xs text-text-muted font-medium uppercase tracking-wider mb-3">
            Performance
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[0.625rem] text-text-muted uppercase tracking-wider mb-1">
                Avg Latency
              </p>
              <p className="text-xl font-semibold text-text-primary tabular-nums">
                {llmMetrics ? formatLatency(llmMetrics.avg_latency) : "—"}
              </p>
            </div>
            <div>
              <p className="text-[0.625rem] text-text-muted uppercase tracking-wider mb-1">
                Last Check
              </p>
              <p className="text-xl font-semibold text-text-primary tabular-nums">
                {llmHealth ? formatLatency(llmHealth.latency_ms) : "—"}
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
