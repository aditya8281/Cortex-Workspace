"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { dashboardApi, type SystemMetrics } from "../api";

function MetricCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: number;
  unit: string;
}) {
  return (
    <Card className="p-4">
      <p className="text-xs text-text-muted mb-1">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className="text-headline font-semibold text-text-primary tabular-nums">
          {unit === "%" ? Math.round(value) : value.toLocaleString()}
        </span>
        <span className="text-xs text-text-muted">{unit}</span>
      </div>
    </Card>
  );
}

export function MetricsRow() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    dashboardApi
      .getMetrics()
      .then((data) => {
        if (!cancelled) setMetrics(data);
      })
      .catch(() => {
        if (!cancelled) setMetrics(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="p-4">
            <div className="h-3 w-16 shimmer-bg rounded" />
            <div className="mt-2 h-6 w-10 shimmer-bg rounded" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <MetricCard label="CPU" value={metrics?.cpu_percent ?? 0} unit="%" />
      <MetricCard label="Memory" value={metrics?.memory_percent ?? 0} unit="%" />
      <MetricCard label="Disk" value={metrics?.disk_percent ?? 0} unit="%" />
      <MetricCard label="Connections" value={metrics?.active_connections ?? 0} unit="active" />
      <MetricCard label="Requests" value={metrics?.requests_today ?? 0} unit="today" />
      <MetricCard label="Avg Latency" value={metrics?.avg_response_ms ?? 0} unit="ms" />
    </div>
  );
}
