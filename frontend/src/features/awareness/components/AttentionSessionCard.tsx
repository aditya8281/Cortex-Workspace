"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { AttentionSession } from "../contextApi";

// ── Helpers ────────────────────────────────────────────────────────────────

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function focusColor(score: number): "success" | "warning" | "danger" {
  if (score >= 80) return "success";
  if (score >= 50) return "warning";
  return "danger";
}

function sessionTypeBadge(type: string) {
  const map: Record<string, "default" | "success" | "warning" | "danger"> = {
    deep_work: "default",
    research: "success",
    coding: "warning",
    review: "danger",
  };
  return map[type] ?? "default";
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-5 w-14" />
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </Card>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

interface AttentionSessionCardProps {
  session: AttentionSession;
  onEnd?: (id: number) => void;
  ending?: boolean;
}

export function AttentionSessionCard({
  session,
  onEnd,
  ending = false,
}: AttentionSessionCardProps) {
  const isActive = !session.ended_at;
  const color = focusColor(session.focus_score);

  const barColor =
    color === "danger"
      ? "bg-danger"
      : color === "warning"
        ? "bg-warning"
        : "bg-success";

  return (
    <Card role="article" aria-label={`Attention session: ${session.session_type}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Type + Status */}
          <div className="flex items-center gap-2 mb-2">
            <Badge variant={sessionTypeBadge(session.session_type)}>
              {session.session_type.replace(/_/g, " ")}
            </Badge>
            {isActive && (
              <Badge variant="success">ACTIVE</Badge>
            )}
          </div>

          {/* Task */}
          {session.task_description && (
            <p className="text-body text-text-secondary line-clamp-2 mb-3">
              {session.task_description}
            </p>
          )}

          {/* Focus Score Bar */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-label uppercase text-text-muted tracking-wider">
                Focus
              </span>
              <span className="font-mono text-sm text-text-primary">
                {session.focus_score}/100
              </span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-bg-surface overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                style={{ width: `${session.focus_score}%` }}
              />
            </div>
          </div>

          {/* Meta Row */}
          <div className="flex items-center gap-4 mt-3 text-xs text-text-muted">
            <span className="font-mono">{formatTime(session.started_at)}</span>
            {session.duration_minutes != null && (
              <span className="font-mono">{session.duration_minutes}m</span>
            )}
            {isActive && session.ended_at == null && (
              <span className="flex items-center gap-1">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-pulse-dot rounded-full bg-success opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-success" />
                </span>
                running
              </span>
            )}
          </div>
        </div>

        {/* End Button */}
        {isActive && onEnd && (
          <button
            onClick={() => onEnd(session.id)}
            disabled={ending}
            className="shrink-0 px-3 py-1.5 rounded-md text-xs font-medium bg-danger/10 text-danger hover:bg-danger/20 disabled:opacity-40 disabled:pointer-events-none transition-colors duration-150"
          >
            {ending ? "Ending..." : "End"}
          </button>
        )}
      </div>
    </Card>
  );
}
