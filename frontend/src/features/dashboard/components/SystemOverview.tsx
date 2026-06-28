"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";
import { dashboardApi, type HealthStatus } from "../api";

const statusColors: Record<string, "success" | "warning" | "danger"> = {
  healthy: "success",
  connected: "success",
  degraded: "warning",
  down: "danger",
  disconnected: "danger",
};

function StatusCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  const color = statusColors[value] ?? "warning";
  return (
    <Card className="p-4" hover>
      <div className="flex items-center gap-2.5">
        <StatusDot color={color} pulse={color === "success"} />
        <div>
          <p className="text-xs text-text-muted">{label}</p>
          <p className="text-sm font-medium text-text-primary capitalize">{value}</p>
        </div>
      </div>
    </Card>
  );
}

export function SystemOverview() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    dashboardApi
      .getHealth()
      .then((data) => {
        if (!cancelled) setHealth(data);
      })
      .catch(() => {
        if (!cancelled) setHealth(null);
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
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-4">
            <div className="h-3 w-16 shimmer-bg rounded" />
            <div className="mt-2 h-4 w-12 shimmer-bg rounded" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatusCard label="System" value={health?.status ?? "down"} />
      <StatusCard label="Database" value={health?.database ?? "disconnected"} />
      <StatusCard label="Redis" value={health?.redis ?? "disconnected"} />
      <StatusCard label="Uptime" value={formatUptime(health?.uptime_seconds ?? 0)} />
    </div>
  );
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}
