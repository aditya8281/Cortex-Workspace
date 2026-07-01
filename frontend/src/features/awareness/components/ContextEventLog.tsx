"use client";

import { useEffect, useState, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { contextEventsApi, type ContextEvent } from "../contextApi";

// ── Helpers ────────────────────────────────────────────────────────────────

function eventTypeBadge(type: string) {
  const map: Record<string, "default" | "success" | "warning" | "danger"> = {
    rule_fired: "success",
    state_changed: "default",
    attention_shift: "warning",
    anomaly_detected: "danger",
    system_event: "default",
  };
  return map[type] ?? "default";
}

function relevanceColor(score: number): "success" | "warning" | "danger" {
  if (score >= 0.8) return "success";
  if (score >= 0.5) return "warning";
  return "danger";
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonLog() {
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <Card key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="h-5 w-5 shrink-0 rounded" />
          <Skeleton className="h-3 w-24 shrink-0" />
          <Skeleton className="h-3 flex-1" />
          <Skeleton className="h-3 w-12 shrink-0" />
          <Skeleton className="h-3 w-16 shrink-0" />
        </Card>
      ))}
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

interface ContextEventLogProps {
  limit?: number;
  filterType?: string;
  onFilterChange?: (type: string | undefined) => void;
}

export function ContextEventLog({
  limit = 50,
  filterType,
  onFilterChange,
}: ContextEventLogProps) {
  const [events, setEvents] = useState<ContextEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    let cancelled = false;
    try {
      const data = await contextEventsApi.list({
        event_type: filterType,
        limit,
      });
      if (!cancelled) {
        setEvents(data);
        setError(null);
      }
    } catch (err: any) {
      if (!cancelled) setError(err.message ?? "Failed to load events");
    }
    return () => {
      cancelled = true;
    };
  }, [filterType, limit]);

  useEffect(() => {
    const cleanup = fetchEvents();
    return () => {
      cleanup.then((fn) => fn?.());
    };
  }, [fetchEvents]);

  if (error) {
    return (
      <Card className="text-center py-8">
        <p className="text-sm text-danger">{error}</p>
        <button
          onClick={() => fetchEvents()}
          className="mt-3 px-3 py-1.5 rounded-md text-xs font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
        >
          Retry
        </button>
      </Card>
    );
  }

  if (!events) return <SkeletonLog />;

  if (events.length === 0) {
    return (
      <EmptyState
        icon={
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        title="No context events"
        description="Events will appear here as context rules fire and state changes occur."
      />
    );
  }

  return (
    <div className="space-y-2">
      {/* Filter Bar */}
      {onFilterChange && (
        <div className="flex items-center gap-2 pb-2">
          <span className="text-label uppercase text-text-muted tracking-wider text-[0.625rem]">
            Filter
          </span>
          <button
            onClick={() => onFilterChange(undefined)}
            className={`px-2 py-1 rounded text-xs font-medium motion-safe:transition-colors motion-safe:duration-150 ${
              !filterType
                ? "bg-accent/12 text-accent"
                : "bg-bg-surface text-text-muted hover:text-text-primary"
            }`}
          >
            All
          </button>
          {["rule_fired", "state_changed", "attention_shift", "anomaly_detected", "system_event"].map(
            (type) => (
              <button
                key={type}
                onClick={() => onFilterChange(type)}
                className={`px-2 py-1 rounded text-xs font-medium motion-safe:transition-colors motion-safe:duration-150 ${
                  filterType === type
                    ? "bg-accent/12 text-accent"
                    : "bg-bg-surface text-text-muted hover:text-text-primary"
                }`}
              >
                {type.replace(/_/g, " ")}
              </button>
            ),
          )}
        </div>
      )}

      {/* Event List */}
      {events.map((event) => (
        <Card
          key={event.id}
          role="article"
          aria-label={`Context event: ${event.event_type}`}
          className="flex items-center gap-3 p-3"
        >
          {/* Relevance Indicator */}
          <div
            className={`h-2 w-2 shrink-0 rounded-full ${
              relevanceColor(event.relevance_score) === "danger"
                ? "bg-danger"
                : relevanceColor(event.relevance_score) === "warning"
                  ? "bg-warning"
                  : "bg-success"
            }`}
            title={`Relevance: ${(event.relevance_score * 100).toFixed(0)}%`}
          />

          {/* Type Badge */}
          <Badge variant={eventTypeBadge(event.event_type)}>
            {event.event_type.replace(/_/g, " ")}
          </Badge>

          {/* Event Data */}
          <div className="min-w-0 flex-1">
            <p className="font-mono text-xs text-text-secondary truncate">
              {Object.keys(event.event_data).length > 0
                ? JSON.stringify(event.event_data)
                : "—"}
            </p>
          </div>

          {/* Source */}
          <span className="text-xs text-text-muted shrink-0 hidden sm:inline">
            {event.source}
          </span>

          {/* Related Rule */}
          {event.related_rule_id != null && (
            <span className="text-[0.625rem] text-accent font-mono shrink-0 hidden md:inline">
              rule:{event.related_rule_id}
            </span>
          )}

          {/* Relevance Score */}
          <span className="font-mono text-xs text-text-muted shrink-0 hidden sm:inline">
            {(event.relevance_score * 100).toFixed(0)}%
          </span>

          {/* Time */}
          <span className="text-xs text-text-muted shrink-0 font-mono" title={formatTime(event.created_at)}>
            {relativeTime(event.created_at)}
          </span>
        </Card>
      ))}
    </div>
  );
}
