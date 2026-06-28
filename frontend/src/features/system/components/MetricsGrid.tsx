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

export function MetricsGrid({ metrics }: { metrics: Record<string, number> }) {
  const cpuColor = getMetricColor(metrics.cpu_percent ?? 0, [60, 85]);
  const memColor = getMetricColor(metrics.memory_percent ?? 0, [70, 90]);

  const items: Metric[] = [
    { label: "CPU", value: metrics.cpu_percent ?? 0, unit: "%", color: cpuColor },
    { label: "Memory", value: metrics.memory_percent ?? 0, unit: "%", color: memColor },
    { label: "Disk", value: metrics.disk_percent ?? 0, unit: "%" },
    { label: "Connections", value: metrics.active_connections ?? 0, unit: "" },
    { label: "Requests", value: metrics.requests_today ?? 0, unit: "today" },
    { label: "Avg Response", value: metrics.avg_response_ms ?? 0, unit: "ms" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {items.map((item) => (
        <MetricCard key={item.label} metric={item} />
      ))}
    </div>
  );
}
