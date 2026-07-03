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

/** Dimmed inline tool display — Claude Code style. Minimal, uniform, subtle. */
export function ToolActivity({ tool, args, result, denied, status, callId, onApprove }: ToolEvent) {
  const [expanded, setExpanded] = useState(false);

  // All statuses use the same dim styling — only the icon changes.
  const statusIcon = denied ? (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="opacity-50">
      <path d="M5 5l6 6M11 5l-6 6" />
    </svg>
  ) : status === "done" ? (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="opacity-60">
      <path d="M5 8l2 2 4-4" />
    </svg>
  ) : status === "approval" ? (
    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="opacity-50">
      <path d="M8 5v3M8 11h.01" />
    </svg>
  ) : (
    <span className="relative flex h-2 w-2">
      <span className="inline-flex h-2 w-2 rounded-full opacity-40 motion-safe:animate-pulse" />
    </span>
  );

  const toolLabel = tool.replace(/_/g, " ");
  const hasResult = !!result && result.length > 0;

  return (
    <div className="flex flex-col gap-px animate-fade-in">
      <div className="flex items-center gap-1.5">
        {/* Status icon */}
        <span className="flex items-center shrink-0 text-text-muted/40">
          {statusIcon}
        </span>

        {/* Tool name */}
        <span className={cn(
          "text-[12px] font-mono tracking-tight",
          status === "calling" ? "text-text-muted/60" :
          status === "done" ? "text-text-muted/50" :
          denied ? "text-text-muted/35" :
          "text-text-muted/60",
        )}>
          {toolLabel}
        </span>

        {/* Args as inline dim text */}
        {args && Object.keys(args).length > 0 && (
          <span className="text-[11px] font-mono text-text-muted/30 truncate max-w-[240px]">
            {Object.entries(args)
              .filter(([, v]) => typeof v === "string" && v.length < 80)
              .map(([k, v]) => `${k}=${v}`)
              .join(", ")}
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

        {/* Approval buttons — very dim, only show on hover emphasis */}
        {status === "approval" && callId && onApprove && (
          <div className="flex gap-1 ml-auto">
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(callId, true); }}
              className="rounded px-1.5 py-0.5 text-[10px] font-mono bg-accent-emerald/8 text-accent-emerald/50 border border-accent-emerald/10 hover:bg-accent-emerald/20 hover:text-accent-emerald/80 motion-safe:transition-colors"
            >
              Allow
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(callId, false); }}
              className="rounded px-1.5 py-0.5 text-[10px] font-mono bg-accent-red/8 text-accent-red/50 border border-accent-red/10 hover:bg-accent-red/20 hover:text-accent-red/80 motion-safe:transition-colors"
            >
              Deny
            </button>
          </div>
        )}
      </div>

      {/* Expandable result — very dim */}
      {hasResult && (
        <div
          className={cn(
            "grid transition-[grid-template-rows] duration-200",
            "motion-safe:[transition-timing-function:cubic-bezier(0.16,1,0.3,1)]",
            expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
          )}
        >
          <div className="overflow-hidden">
            <div className="ml-3.5 pl-1.5 border-l border-text-muted/8 py-1">
              <pre className="text-[11px] font-mono leading-relaxed text-text-muted/35 whitespace-pre-wrap overflow-x-auto max-h-32 overflow-y-auto">
                {result}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
