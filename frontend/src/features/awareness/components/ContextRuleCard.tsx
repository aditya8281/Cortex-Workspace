"use client";

import { useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { ContextRule } from "../contextApi";

// ── Helpers ────────────────────────────────────────────────────────────────

function ruleTypeBadge(type: string) {
  const map: Record<string, "default" | "success" | "warning" | "danger"> = {
    trigger: "default",
    filter: "success",
    transform: "warning",
    guard: "danger",
  };
  return map[type] ?? "default";
}

function formatTime(iso: string | null): string {
  if (!iso) return "never";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-5 w-14" />
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </Card>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

interface ContextRuleCardProps {
  rule: ContextRule;
  onToggle?: (id: number, enabled: boolean) => void;
  onEdit?: (rule: ContextRule) => void;
  onDelete?: (id: number) => void;
  toggling?: boolean;
}

export function ContextRuleCard({
  rule,
  onToggle,
  onEdit,
  onDelete,
  toggling = false,
}: ContextRuleCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <Card role="article" aria-label={`Context rule: ${rule.name}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-title font-medium text-text-primary truncate">
              {rule.name}
            </h4>
            <Badge variant={ruleTypeBadge(rule.rule_type)}>
              {rule.rule_type}
            </Badge>
          </div>

          {rule.description && (
            <p className="text-body text-text-secondary text-sm line-clamp-2 mb-2">
              {rule.description}
            </p>
          )}
        </div>

        {/* Enabled Toggle */}
        {onToggle && (
          <button
            onClick={() => onToggle(rule.id, !rule.enabled)}
            disabled={toggling}
            className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full motion-safe:transition-colors motion-safe:duration-150 focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none ${
              rule.enabled
                ? "bg-accent"
                : "bg-bg-surface border border-border-subtle"
            } ${toggling ? "opacity-40 pointer-events-none" : ""}`}
            aria-label={`Toggle ${rule.name}`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white motion-safe:transition-transform duration-150 ${
                rule.enabled ? "translate-x-[18px]" : "translate-x-[3px]"
              }`}
            />
          </button>
        )}
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-4 mt-3 text-xs text-text-muted">
        <span className="font-mono">
          Priority: {rule.priority}
        </span>
        <span className="font-mono">
          Hits: {rule.hit_count}
        </span>
        <span className="font-mono">
          Last hit: {formatTime(rule.last_hit_at)}
        </span>
      </div>

      {/* Conditions/Actions Preview */}
      {(Object.keys(rule.conditions).length > 0 ||
        Object.keys(rule.actions).length > 0) && (
        <div className="mt-3 space-y-1.5">
          {Object.keys(rule.conditions).length > 0 && (
            <div>
              <span className="text-label uppercase text-text-muted tracking-wider text-[0.625rem]">
                Conditions
              </span>
              <pre className="font-mono text-xs text-text-secondary bg-bg-surface rounded px-2 py-1 mt-1 overflow-x-auto">
                {JSON.stringify(rule.conditions, null, 2)}
              </pre>
            </div>
          )}
          {Object.keys(rule.actions).length > 0 && (
            <div>
              <span className="text-label uppercase text-text-muted tracking-wider text-[0.625rem]">
                Actions
              </span>
              <pre className="font-mono text-xs text-text-secondary bg-bg-surface rounded px-2 py-1 mt-1 overflow-x-auto">
                {JSON.stringify(rule.actions, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border-subtle">
        {onEdit && (
          <button
            onClick={() => onEdit(rule)}
            className="px-3 py-1.5 rounded-md text-xs font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
          >
            Edit
          </button>
        )}
        {onDelete && (
          <>
            {confirmDelete ? (
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-danger">Delete?</span>
                <button
                  onClick={() => {
                    onDelete(rule.id);
                    setConfirmDelete(false);
                  }}
                  className="px-2 py-1 rounded text-xs font-medium bg-danger/10 text-danger hover:bg-danger/20 motion-safe:transition-colors motion-safe:duration-150"
                >
                  Yes
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="px-2 py-1 rounded text-xs font-medium bg-bg-surface text-text-muted hover:text-text-primary motion-safe:transition-colors motion-safe:duration-150"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="px-3 py-1.5 rounded-md text-xs font-medium bg-danger/10 text-danger hover:bg-danger/20 motion-safe:transition-colors motion-safe:duration-150"
              >
                Delete
              </button>
            )}
          </>
        )}
      </div>
    </Card>
  );
}
