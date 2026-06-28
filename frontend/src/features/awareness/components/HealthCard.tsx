"use client";

import { useState, useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";
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

function Skeleton() {
  return (
    <Card role="article" aria-label="Health info loading">
      <div className="animate-pulse space-y-3">
        <div className="h-4 w-28 rounded bg-bg-surface" />
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-bg-surface" />
          <div className="h-3 w-20 rounded bg-bg-surface" />
        </div>
        <div className="h-3 w-36 rounded bg-bg-surface" />
        <div className="h-3 w-24 rounded bg-bg-surface" />
        <div className="h-3 w-44 rounded bg-bg-surface" />
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

  if (!data) return <Skeleton />;

  const color = statusColor(data.status);

  return (
    <Card role="article" aria-label="Health info">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-text-primary">Health</h3>

        {/* Status */}
        <div className="flex items-center gap-2">
          <StatusDot color={color} pulse={data.status.toLowerCase() === "healthy"} />
          <span className={`text-xs font-semibold capitalize text-${color}`}>
            {statusLabel(data.status)}
          </span>
        </div>

        {/* Indexing Active */}
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span className="font-medium text-text-muted">Indexing:</span>
          {data.indexing_active ? (
            <StatusDot color="success" pulse />
          ) : (
            <StatusDot color="warning" />
          )}
          <span>{data.indexing_active ? "Active" : "Inactive"}</span>
        </div>

        {/* Watched Count */}
        <p className="text-xs text-text-secondary">
          <span className="font-medium text-text-muted">Watched:</span>{" "}
          {data.watched_count} {data.watched_count === 1 ? "directory" : "directories"}
        </p>

        {/* Last Scan */}
        <p className="text-xs text-text-secondary">
          <span className="font-medium text-text-muted">Last scan:</span>{" "}
          {data.last_scan ? formatTime(data.last_scan) : "Never"}
        </p>
      </div>
    </Card>
  );
}
