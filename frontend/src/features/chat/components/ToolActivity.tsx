"use client";

import { useState } from "react";
import { cn } from "@/shared/lib/utils";

export interface ToolEvent {
  tool: string;
  args?: Record<string, string>;
  result?: string;
  denied?: boolean;
  status: "calling" | "done" | "denied" | "approval";
  callId?: string;
  onApprove?: (callId: string, approved: boolean) => void;
}

/** Status icon mapping — subtle, dim, consistent with Claude Code style. */
function StatusIcon({ status, denied }: { status: ToolEvent["status"]; denied?: boolean }) {
  if (denied) {
    return (
      <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M5 5l6 6M11 5l-6 6" />
      </svg>
    );
  }
  switch (status) {
    case "done":
      return (
        <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M5 8l2 2 4-4" />
        </svg>
      );
    case "approval":
      return (
        <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M8 5v3M8 11h.01" />
        </svg>
      );
    default:
      return (
        <span className="relative flex h-2 w-2">
          <span className="inline-flex h-2 w-2 rounded-full motion-safe:animate-pulse" />
        </span>
      );
  }
}

export function ToolActivity({ tool, args, result, denied, status, callId, onApprove }: ToolEvent) {
  const [expanded, setExpanded] = useState(false);

  const toolLabel = tool.replace(/_/g, " ");
  const hasResult = !!result && result.length > 0;

  // ── Border accent color by status ──────────────────────────────────────
  const borderAccent = denied
    ? "border-l-accent-red/30"
    : status === "done"
      ? "border-l-accent-emerald/30"
      : status === "approval"
        ? "border-l-amber-500/25"
        : "border-l-accent-cyan/25";

  // ── Background dimness by status ──────────────────────────────────────
  const bgDim = denied
    ? "bg-bg-elevated/30"
    : status === "done"
      ? "bg-bg-elevated/40"
      : "bg-bg-elevated/20";

  return (
    <div
      className={cn(
        "group flex flex-col rounded-lg border border-border-subtle/50",
        "border-l-2 motion-safe:transition-all motion-safe:duration-200",
        "hover:border-border-subtle",
        borderAccent,
        bgDim,
      )}
      // Stagger entrance via style — each gets a progressive delay
      style={{
        // Used by CSS if animate-stagger class is present
        viewTransitionName: `tool-${tool}`,
      }}
    >
      {/* ── Main row: icon + tool name + args + status + expand ──────── */}
      <div className="flex items-center gap-1.5 px-2.5 py-1.5 min-h-[28px]">
        {/* Status icon */}
        <span className={cn(
          "flex items-center shrink-0",
          denied ? "text-accent-red/40" :
          status === "done" ? "text-accent-emerald/40" :
          status === "approval" ? "text-amber-400/40" :
          "text-accent-cyan/50",
        )}>
          <StatusIcon status={status} denied={denied} />
        </span>

        {/* Tool name */}
        <span className={cn(
          "text-[12px] font-mono tracking-tight font-medium",
          denied ? "text-accent-red/50" :
          status === "done" ? "text-text-muted/60" :
          status === "approval" ? "text-text-muted/55" :
          "text-text-muted/65",
        )}>
          {toolLabel}
        </span>

        {/* Args as inline dim text */}
        {args && Object.keys(args).length > 0 && (
          <span className="text-[11px] font-mono text-text-muted/30 truncate max-w-[320px]">
            {Object.entries(args)
              .filter(([, v]) => typeof v === "string" && v.length < 80)
              .map(([k, v]) => `${k}=${v}`)
              .join(", ")}
          </span>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Status label — very dim, right-aligned */}
        {status === "calling" && (
          <span className="text-[10px] font-mono text-accent-cyan/30 motion-safe:animate-pulse">
            running…
          </span>
        )}
        {status === "approval" && (
          <span className="text-[10px] font-mono text-amber-400/40">
            requires approval
          </span>
        )}

        {/* Expand/collapse toggle for results */}
        {hasResult && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-text-muted/20 hover:text-text-muted/50 motion-safe:transition-colors"
          >
            <svg
              width="10" height="10" viewBox="0 0 16 16"
              fill="none" stroke="currentColor" strokeWidth="1.5"
              className={cn("motion-safe:transition-transform duration-150", expanded && "rotate-90")}
            >
              <path d="M6 4l4 4-4 4" />
            </svg>
          </button>
        )}
      </div>

      {/* ── Expandable result ────────────────────────────────────────── */}
      {hasResult && (
        <div
          className={cn(
            "grid transition-[grid-template-rows] duration-200",
            "motion-safe:[transition-timing-function:cubic-bezier(0.16,1,0.3,1)]",
            expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
          )}
        >
          <div className="overflow-hidden">
            <div className="ml-3.5 pl-1.5 border-l border-text-muted/8 py-1 pr-2.5 pb-2">
              <pre className="text-[11px] font-mono leading-relaxed text-text-muted/35 whitespace-pre-wrap overflow-x-auto max-h-32 overflow-y-auto">
                {result}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* ── Approval buttons — full-width bottom row ─────────────────── */}
      {status === "approval" && callId && onApprove && (
        <div className="flex items-center gap-2 px-2.5 pb-2 pt-0">
          <div className="flex-1" />
          <div className="flex gap-1.5">
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(callId, true); }}
              className={cn(
                "rounded-md px-2.5 py-1 text-[11px] font-medium font-mono tracking-tight",
                "bg-accent-emerald/10 text-accent-emerald/60 border border-accent-emerald/15",
                "hover:bg-accent-emerald/20 hover:text-accent-emerald/80",
                "motion-safe:transition-colors motion-safe:duration-150",
              )}
            >
              Allow
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(callId, false); }}
              className={cn(
                "rounded-md px-2.5 py-1 text-[11px] font-medium font-mono tracking-tight",
                "bg-accent-red/10 text-accent-red/50 border border-accent-red/15",
                "hover:bg-accent-red/20 hover:text-accent-red/80",
                "motion-safe:transition-colors motion-safe:duration-150",
              )}
            >
              Deny
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
