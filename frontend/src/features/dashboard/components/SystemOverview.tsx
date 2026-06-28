"use client";

import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { useMetrics } from "@/shared/ws/MetricsProvider";

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
  const { metrics, connected } = useMetrics();

  if (!connected || !metrics) {
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
            metrics.gpu_name && metrics.gpu_name !== "No GPU detected"
              ? `${metrics.gpu_percent?.toFixed(1) ?? "0.0"}%`
              : "Not available"
          }
          percent={metrics.gpu_percent ?? 0}
          sublabel={metrics.gpu_name !== "No GPU detected" ? metrics.gpu_name : undefined}
        />
        <MetricProgressCard
          label="Disk"
          value={`${metrics.disk_used_gb.toFixed(0)} / ${metrics.disk_total_gb.toFixed(0)} GB`}
          percent={metrics.disk_percent}
        />
      </div>
    </div>
  );
}
