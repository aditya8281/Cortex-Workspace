"use client";

import { useEffect, useState, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { contextStateApi, type ContextState } from "../contextApi";

// ── Helpers ────────────────────────────────────────────────────────────────

function confidenceColor(c: number): "success" | "warning" | "danger" {
  if (c >= 0.8) return "success";
  if (c >= 0.5) return "warning";
  return "danger";
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Card key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </Card>
      ))}
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

export function ContextStatePanel() {
  const [states, setStates] = useState<ContextState[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  const fetchStates = useCallback(async () => {
    let cancelled = false;
    try {
      const data = await contextStateApi.list();
      if (!cancelled) {
        setStates(data);
        setError(null);
      }
    } catch (err: any) {
      if (!cancelled) setError(err.message ?? "Failed to load states");
    }
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const cleanup = fetchStates();
    return () => {
      cleanup.then((fn) => fn?.());
    };
  }, [fetchStates]);

  if (error) {
    return (
      <Card className="text-center py-8">
        <p className="text-sm text-danger">{error}</p>
        <button
          onClick={() => fetchStates()}
          className="mt-3 px-3 py-1.5 rounded-md text-xs font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
        >
          Retry
        </button>
      </Card>
    );
  }

  if (!states) return <SkeletonGrid />;

  if (states.length === 0) {
    return (
      <EmptyState
        icon={
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M4 7V4h16v3M9 20h6M12 4v16" />
          </svg>
        }
        title="No context states"
        description="Context states will appear here as the system builds awareness."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {states.map((state) => {
        const isExpanded = expandedKey === state.state_key;
        const valueStr = JSON.stringify(state.state_value, null, 2);
        const isLong = valueStr.split("\n").length > 3;

        return (
          <Card
            key={state.state_key}
            role="article"
            aria-label={`Context state: ${state.state_key}`}
            hover
            className="space-y-2 cursor-pointer"
            onClick={() =>
              setExpandedKey(isExpanded ? null : state.state_key)
            }
          >
            {/* Key Header */}
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-sm text-accent truncate">
                {state.state_key}
              </span>
              <Badge variant={confidenceColor(state.confidence)}>
                {(state.confidence * 100).toFixed(0)}%
              </Badge>
            </div>

            {/* Value */}
            <pre
              className={`font-mono text-xs text-text-secondary bg-bg-surface rounded px-2 py-1 overflow-x-auto motion-safe:transition-all motion-safe:duration-200 ${
                isExpanded || !isLong ? "max-h-none" : "max-h-16 overflow-hidden"
              }`}
            >
              {valueStr}
            </pre>
            {isLong && (
              <span className="text-[0.625rem] text-text-muted">
                {isExpanded ? "Click to collapse" : "Click to expand"}
              </span>
            )}

            {/* Source + Timestamp */}
            <div className="flex items-center gap-3 text-xs text-text-muted pt-1">
              <span>Source: {state.source}</span>
              <span className="font-mono">{formatTime(state.updated_at)}</span>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
