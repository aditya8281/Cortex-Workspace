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

/** Compact inline display of a tool being used — shows during streaming. */
export function ToolActivity({ tool, args, result, denied, status, callId, onApprove }: ToolEvent) {
  const [expanded, setExpanded] = useState(false);

  const statusIcon = denied ? (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="8" cy="8" r="6" />
      <path d="M5 5l6 6M11 5l-6 6" />
    </svg>
  ) : status === "done" ? (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="8" cy="8" r="6" />
      <path d="M5 8l2 2 4-4" />
    </svg>
  ) : status === "approval" ? (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="8" cy="8" r="6" />
      <path d="M8 5v3M8 11h.01" />
    </svg>
  ) : (
    <span className="relative flex h-2 w-2 shrink-0">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-cyan opacity-40" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-cyan/60" />
    </span>
  );

  const statusColor = denied
    ? "text-accent-red border-accent-red/15 bg-accent-red-muted/8"
    : status === "done"
    ? "text-accent-emerald border-accent-emerald/15 bg-accent-emerald-muted/8"
    : status === "approval"
    ? "text-accent-amber border-accent-amber/15 bg-accent-amber-muted/8"
    : "text-accent-cyan border-accent-cyan/15 bg-accent-cyan-muted/8";

  const toolLabel = tool.replace(/_/g, " ");
  const hasResult = !!result && result.length > 0;

  return (
    <div className="flex flex-col gap-1 animate-fade-in">
      <button
        onClick={() => hasResult && setExpanded(!expanded)}
        className={cn(
          "flex items-center gap-2 rounded-lg px-3 py-1.5",
          "text-[11px] font-mono tracking-tight border",
          statusColor,
          hasResult && "cursor-pointer hover:opacity-80",
          "motion-safe:transition-all motion-safe:duration-150",
        )}
      >
        {statusIcon}
        <span className="font-medium">{toolLabel}</span>
        {args && Object.keys(args).length > 0 && (
          <span className="text-[10px] opacity-60 truncate max-w-[200px]">
            {Object.entries(args).map(([k, v]) => `${k}=${v}`).join(", ")}
          </span>
        )}
        {status === "approval" && callId && onApprove && (
          <div className="flex gap-1 ml-2">
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(callId, true); }}
              className="rounded px-2 py-0.5 text-[10px] bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/20 hover:bg-accent-emerald/30 motion-safe:active:scale-95"
            >
              Allow
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(callId, false); }}
              className="rounded px-2 py-0.5 text-[10px] bg-accent-red/20 text-accent-red border border-accent-red/20 hover:bg-accent-red/30 motion-safe:active:scale-95"
            >
              Deny
            </button>
          </div>
        )}
      </button>

      {/* Expandable result */}
      {hasResult && (
        <div
          className={cn(
            "grid transition-[grid-template-rows] duration-200",
            "motion-safe:[transition-timing-function:cubic-bezier(0.16,1,0.3,1)]",
            expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
          )}
        >
          <div className="overflow-hidden">
            <div className={cn(
              "ml-3 max-h-32 overscroll-contain",
              "rounded-lg border border-border-subtle bg-bg-elevated/30",
              "px-3 py-2 text-[11px] leading-relaxed text-text-muted",
              "font-mono whitespace-pre-wrap overflow-y-auto",
            )}>
              {result}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
