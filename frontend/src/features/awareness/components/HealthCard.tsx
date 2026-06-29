"use client";

import { useState, useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Skeleton } from "@/shared/ui/Skeleton";
import { awarenessHealth, type AwarenessHealth } from "@/features/awareness/api";

// ── Helpers ─────────────────────────────────────────────────────────────────

type StatusColor = "success" | "warning" | "danger";

function statusColor(status: string): StatusColor {
  switch (status.toLowerCase()) {
    case "healthy":
      return "success";
    case "degraded":
      return "warning";
    default:
      return "danger";
  }
}

function statusLabel(status: string): string {
  switch (status.toLowerCase()) {
    case "healthy":
      return "Healthy";
    case "degraded":
      return "Degraded";
    default:
      return "Error";
  }
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

// ── Skeleton ────────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card role="article" aria-label="Health info loading">
      <div className="space-y-3">
        <Skeleton className="h-4 w-28" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-2 w-2 rounded-full" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="h-3 w-36" />
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-44" />
      </div>
    </Card>
  );
}

// ── Component ───────────────────────────────────────────────────────────────

export function HealthCard() {
  const [data, setData] = useState<AwarenessHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    awarenessHealth
      .check()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load health info");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <Card role="article" aria-label="Health info error">
        <p className="text-xs text-danger">{error}</p>
      </Card>
    );
  }

  if (!data) return <SkeletonCard />;

  const color = statusColor(data.overall_status ?? "error");

  return (
    <Card role="article" aria-label="Health info">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-text-primary">Health</h3>

        {/* Overall Status */}
        <div className="flex items-center gap-2">
          <StatusDot color={color} pulse={data.overall_status === "healthy"} />
          <span className={`text-xs font-semibold capitalize text-${color}`}>
            {statusLabel(data.overall_status)}
          </span>
        </div>

        {/* Services */}
        {data.services?.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-text-muted">Services</p>
            {data.services.map(s => (
              <div key={s.id} className="flex items-center gap-2 text-xs text-text-secondary">
                <StatusDot color={s.status === "healthy" ? "success" : s.status === "warning" ? "warning" : "danger"} />
                <span className="font-medium">{s.service_name}</span>
                <span className="text-text-muted">{s.status}</span>
                {s.response_time_ms != null && <span className="text-text-muted">({s.response_time_ms.toFixed(0)}ms)</span>}
              </div>
            ))}
          </div>
        )}

        {/* Summary */}
        {data.summary && Object.keys(data.summary).length > 0 && (
          <p className="text-xs text-text-secondary">
            <span className="font-medium text-text-muted">Total:</span>{" "}
            {data.summary.total ?? data.services?.length ?? 0} service{(data.summary.total ?? 0) !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </Card>
  );
}
