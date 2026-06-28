"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { dashboardApi, type SystemMetrics } from "../api";

function barColor(percent: number): string {
  if (percent < 70) return "bg-success";
  if (percent < 85) return "bg-warning";
  return "bg-danger";
}

function MetricProgressCard({
  label,
  value,
  percent,
  sublabel,
}: {
  label: string;
  value: string;
  percent: number;
  sublabel?: string;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-text-muted font-medium">{label}</p>
        <p className="text-xs text-text-muted">{percent.toFixed(1)}%</p>
      </div>
      <p className="text-lg font-semibold text-text-primary tabular-nums mb-3">
        {value}
      </p>
      {sublabel && (
        <p className="text-xs text-text-muted mb-2">{sublabel}</p>
      )}
      <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor(percent)} transition-[width] duration-500 ease-out`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </Card>
  );
}

export function SystemOverview() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchMetrics = () => {
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
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <Skeleton className="h-3 w-12" />
                <Skeleton className="h-3 w-8" />
              </div>
              <Skeleton className="h-6 w-20 mb-3" />
              <Skeleton className="h-1.5 w-full rounded-full" />
            </Card>
          ))}
        </div>
        <Card className="p-4">
          <Skeleton className="h-4 w-24 mb-3" />
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (!metrics) {
    return (
      <Card className="p-4">
        <p className="text-sm text-text-muted">Unable to load system metrics.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricProgressCard
          label="CPU"
          value={`${metrics.cpu_percent.toFixed(1)}%`}
          percent={metrics.cpu_percent}
        />
        <MetricProgressCard
          label="RAM"
          value={`${metrics.ram_used_gb.toFixed(1)} / ${metrics.ram_total_gb.toFixed(0)} GB`}
          percent={metrics.ram_percent}
        />
        <MetricProgressCard
          label="GPU"
          value={
            metrics.gpu_name
              ? `${metrics.gpu_percent?.toFixed(1) ?? "0.0"}%`
              : "Not available"
          }
          percent={metrics.gpu_percent ?? 0}
          sublabel={metrics.gpu_name ?? undefined}
        />
        <MetricProgressCard
          label="Disk"
          value={`${metrics.disk_used_gb.toFixed(0)} / ${metrics.disk_total_gb.toFixed(0)} GB`}
          percent={metrics.disk_percent}
        />
      </div>

      {(metrics.processes ?? []).length > 0 && (
        <Card className="p-4">
          <p className="text-xs text-text-muted font-medium mb-3">Top Processes</p>
          <div className="space-y-1.5">
            {metrics.processes.slice(0, 5).map((proc) => (
              <div
                key={proc.pid}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-text-primary font-mono truncate max-w-[180px]">
                  {proc.name}
                </span>
                <span className="text-text-muted tabular-nums whitespace-nowrap">
                  CPU {proc.cpu.toFixed(1)}% &middot; MEM {proc.memory.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
