"use client";

import { Card } from "@/shared/ui/Card";

interface Metric {
  label: string;
  value: string | number;
  unit: string;
  color?: "accent" | "success" | "warning" | "danger";
}

const colorMap: Record<string, string> = {
  accent: "text-accent",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

function getMetricColor(value: number, thresholds: [number, number]): "success" | "warning" | "danger" {
  if (value < thresholds[0]) return "success";
  if (value < thresholds[1]) return "warning";
  return "danger";
}

function MetricCard({ metric }: { metric: Metric }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-text-muted mb-1">{metric.label}</p>
      <div className="flex items-baseline gap-1">
        <span className={`text-headline font-semibold tabular-nums ${colorMap[metric.color ?? "accent"]}`}>
          {typeof metric.value === "number" ? Math.round(metric.value) : metric.value}
        </span>
        <span className="text-xs text-text-muted">{metric.unit}</span>
      </div>
    </Card>
  );
}

export interface MetricsData {
  cpu_percent?: number;
  memory_percent?: number;
  gpu_percent?: number;
  disk_percent?: number;
  ram_used_gb?: number;
  ram_total_gb?: number;
  gpu_name?: string;
}

export function MetricsGrid({ metrics }: { metrics: MetricsData }) {
  const cpuColor = getMetricColor(metrics.cpu_percent ?? 0, [60, 85]);
  const memColor = getMetricColor(metrics.memory_percent ?? 0, [70, 90]);
  const diskColor = getMetricColor(metrics.disk_percent ?? 0, [75, 90]);

  const items: Metric[] = [
    { label: "CPU", value: metrics.cpu_percent ?? 0, unit: "%", color: cpuColor },
    { label: "Memory", value: metrics.memory_percent ?? 0, unit: "%", color: memColor },
    { label: "Disk", value: metrics.disk_percent ?? 0, unit: "%", color: diskColor },
    ...(metrics.gpu_percent != null
      ? [{ label: "GPU", value: metrics.gpu_percent, unit: "%", color: getMetricColor(metrics.gpu_percent, [60, 85]) }]
      : []),
    { label: "RAM", value: metrics.ram_used_gb ?? 0, unit: `/ ${metrics.ram_total_gb ?? 0} GB` },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {items.map((item) => (
        <MetricCard key={item.label} metric={item} />
      ))}
    </div>
  );
}
