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

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="p-4">
            <Skeleton className="h-3 w-16 mb-2" />
            <Skeleton className="h-6 w-14" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <Card className="p-4">
        <p className="text-xs text-text-muted mb-1">Total Requests</p>
        <p className="text-headline font-semibold text-text-primary tabular-nums">
          {llmMetrics ? formatCount(llmMetrics.total_requests) : "---"}
        </p>
      </Card>
      <Card className="p-4">
        <p className="text-xs text-text-muted mb-1">Total Tokens</p>
        <p className="text-headline font-semibold text-text-primary tabular-nums">
          {llmMetrics ? formatCount(llmMetrics.total_tokens) : "---"}
        </p>
      </Card>
      <Card className="p-4">
        <p className="text-xs text-text-muted mb-1">Avg Latency</p>
        <p className="text-headline font-semibold text-text-primary tabular-nums">
          {llmMetrics ? `${llmMetrics.avg_latency} ms` : "---"}
        </p>
      </Card>
      <Card className="p-4">
        <p className="text-xs text-text-muted mb-1">LLM Status</p>
        <div className="flex items-center gap-2">
          <StatusDot
            color={statusColor(llmHealth?.status ?? "danger")}
            pulse={llmHealth?.status === "healthy"}
          />
          <span className="text-sm font-medium text-text-primary capitalize">
            {llmHealth?.status ?? "unknown"}
          </span>
        </div>
      </Card>
      <Card className="p-4">
        <p className="text-xs text-text-muted mb-1">LLM Latency</p>
        <p className="text-headline font-semibold text-text-primary tabular-nums">
          {llmHealth ? `${llmHealth.latency_ms} ms` : "---"}
        </p>
      </Card>
    </div>
  );
}
