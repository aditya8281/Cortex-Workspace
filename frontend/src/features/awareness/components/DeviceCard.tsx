"use client";

import { useState, useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { device, type DeviceInfo } from "@/features/awareness/api";

// ── Helpers ─────────────────────────────────────────────────────────────────

function percentUsed(used: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((used / total) * 100);
}

function usageColor(pct: number): string {
  if (pct < 70) return "bg-success";
  if (pct < 85) return "bg-warning";
  return "bg-danger";
}

function formatBytes(bytes: number): string {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unitIdx = 0;
  while (value >= 1024 && unitIdx < units.length - 1) {
    value /= 1024;
    unitIdx++;
  }
  return `${value.toFixed(1)} ${units[unitIdx]}`;
}

// ── Skeleton ────────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card role="article" aria-label="Device info loading">
      <div className="space-y-3">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-48" />
        <Skeleton className="h-3 w-40" />
        <Skeleton className="h-3 w-36" />
        <Skeleton className="h-3 w-44" />
        <div className="space-y-1.5 pt-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-2 w-full" />
        </div>
        <div className="space-y-1.5">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-2 w-full" />
        </div>
      </div>
    </Card>
  );
}

// ── Progress Bar ────────────────────────────────────────────────────────────

function ProgressBar({ pct }: { pct: number }) {
  const color = usageColor(pct);
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-bg-surface">
      <div
        className={`h-full rounded-full ${color} motion-safe:transition-[width] duration-300 ease-out`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ── Component ───────────────────────────────────────────────────────────────

export function DeviceCard() {
  const [data, setData] = useState<DeviceInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    device
      .info()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load device info");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <Card role="article" aria-label="Device info error">
        <p className="text-xs text-danger">{error}</p>
      </Card>
    );
  }

  if (!data) return <SkeletonCard />;

  const ramPct = percentUsed(data.memory_used, data.memory_total);
  const diskPct = percentUsed(data.disk_used, data.disk_total);

  return (
    <Card role="article" aria-label="Device info">
      <div className="space-y-2.5">
        {/* Header */}
        <h3 className="text-sm font-semibold text-text-primary">Device</h3>

        {/* Details */}
        <div className="space-y-1 text-xs text-text-secondary">
          <p>
            <span className="font-medium text-text-primary">Hostname:</span>{" "}
            {data.hostname}
          </p>
          <p>
            <span className="font-medium text-text-primary">OS:</span> {data.os}
          </p>
          <p>
            <span className="font-medium text-text-primary">CPU:</span> {data.cpu}
          </p>
          <p>
            <span className="font-medium text-text-primary">Python:</span>{" "}
            {data.python_version}
          </p>
          <p>
            <span className="font-medium text-text-primary">Cortex:</span>{" "}
            {data.cortex_version}
          </p>
        </div>

        {/* RAM Bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>RAM</span>
            <span>
              {formatBytes(data.memory_used)} / {formatBytes(data.memory_total)} ({ramPct}%)
            </span>
          </div>
          <ProgressBar pct={ramPct} />
        </div>

        {/* Disk Bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>Disk</span>
            <span>
              {formatBytes(data.disk_used)} / {formatBytes(data.disk_total)} ({diskPct}%)
            </span>
          </div>
          <ProgressBar pct={diskPct} />
        </div>
      </div>
    </Card>
  );
}
