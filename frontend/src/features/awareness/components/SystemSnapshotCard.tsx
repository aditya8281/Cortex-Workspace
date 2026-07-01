"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { SystemSnapshot } from "../contextApi";

// ── Helpers ────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hrs = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hrs}h ${mins}m`;
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function metricColor(percent: number): "success" | "warning" | "danger" {
  if (percent >= 90) return "danger";
  if (percent >= 70) return "warning";
  return "success";
}

// ── Metric Pill ────────────────────────────────────────────────────────────

function MetricPill({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "success" | "warning" | "danger";
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-label uppercase text-text-muted tracking-wider">
        {label}
      </span>
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm text-text-primary">{value}</span>
        <Badge variant={color}>
          {color === "danger" ? "HIGH" : color === "warning" ? "MID" : "OK"}
        </Badge>
      </div>
    </div>
  );
}

// ── Bar ────────────────────────────────────────────────────────────────────

function ProgressBar({
  percent,
  color,
}: {
  percent: number;
  color: "success" | "warning" | "danger";
}) {
  const barColor =
    color === "danger"
      ? "bg-danger"
      : color === "warning"
        ? "bg-warning"
        : "bg-success";

  return (
    <div className="h-1.5 w-full rounded-full bg-bg-surface overflow-hidden">
      <div
        className={`h-full rounded-full motion-safe:transition-all duration-500 ${barColor}`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  );
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-5 w-16" />
      </div>
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-1.5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-1.5 w-full" />
          </div>
        ))}
      </div>
      <Skeleton className="h-3 w-40" />
    </Card>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

interface SystemSnapshotCardProps {
  snapshot: SystemSnapshot | null;
  loading?: boolean;
  onTakeSnapshot?: () => void;
  snapshotLoading?: boolean;
}

export function SystemSnapshotCard({
  snapshot,
  loading = false,
  onTakeSnapshot,
  snapshotLoading = false,
}: SystemSnapshotCardProps) {
  if (loading || !snapshot) return <SkeletonCard />;

  const cpuColor = metricColor(snapshot.cpu_percent);
  const memColor = metricColor(snapshot.memory_percent);
  const diskColor = metricColor(snapshot.disk_percent);

  return (
    <Card role="article" aria-label="System snapshot" className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-title font-medium text-text-primary">
          System Snapshot
        </h3>
        <Badge variant={cpuColor}>
          {formatTime(snapshot.created_at)}
        </Badge>
      </div>

      {/* Core Metrics */}
      <div className="space-y-3">
        {/* CPU */}
        <div className="space-y-1.5">
          <MetricPill label="CPU" value={`${snapshot.cpu_percent.toFixed(1)}%`} color={cpuColor} />
          <ProgressBar percent={snapshot.cpu_percent} color={cpuColor} />
        </div>

        {/* Memory */}
        <div className="space-y-1.5">
          <MetricPill
            label="Memory"
            value={`${snapshot.memory_percent.toFixed(1)}% (${snapshot.memory_used_gb.toFixed(1)} / ${snapshot.memory_total_gb.toFixed(1)} GB)`}
            color={memColor}
          />
          <ProgressBar percent={snapshot.memory_percent} color={memColor} />
        </div>

        {/* Disk */}
        <div className="space-y-1.5">
          <MetricPill
            label="Disk"
            value={`${snapshot.disk_percent.toFixed(1)}% (${snapshot.disk_used_gb.toFixed(1)} / ${snapshot.disk_total_gb.toFixed(1)} GB)`}
            color={diskColor}
          />
          <ProgressBar percent={snapshot.disk_percent} color={diskColor} />
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="flex flex-col gap-0.5">
          <span className="text-label uppercase text-text-muted tracking-wider">
            Network
          </span>
          <span className="font-mono text-sm text-text-secondary">
            ↑ {formatBytes(snapshot.network_sent_bytes)} · ↓ {formatBytes(snapshot.network_recv_bytes)}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-label uppercase text-text-muted tracking-wider">
            Load Avg
          </span>
          <span className="font-mono text-sm text-text-secondary">
            {snapshot.load_average_1m.toFixed(2)} / {snapshot.load_average_5m.toFixed(2)} / {snapshot.load_average_15m.toFixed(2)}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-label uppercase text-text-muted tracking-wider">
            Processes
          </span>
          <span className="font-mono text-sm text-text-secondary">
            {snapshot.process_count}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-label uppercase text-text-muted tracking-wider">
            Uptime
          </span>
          <span className="font-mono text-sm text-text-secondary">
            {formatUptime(snapshot.uptime_seconds)}
          </span>
        </div>
      </div>

      {/* Action */}
      {onTakeSnapshot && (
        <button
          onClick={onTakeSnapshot}
          disabled={snapshotLoading}
          className="w-full px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:pointer-events-none motion-safe:transition-colors motion-safe:duration-150"
        >
          {snapshotLoading ? "Capturing..." : "Take Snapshot"}
        </button>
      )}
    </Card>
  );
}
