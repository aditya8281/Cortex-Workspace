"use client";

import { useEffect, useState } from "react";
import { cn } from "@/shared/lib/utils";
import { MarkdownRenderer } from "./MarkdownRenderer";

// ── Chevron icon ──────────────────────────────────────────────────────
function ChevronDown({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="12"
      height="12"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <path d="M4 6l4 4 4-4" />
    </svg>
  );
}

// ── Props ─────────────────────────────────────────────────────────────
interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  thinkingContent?: string;
  timestamp?: string;
  isStreaming?: boolean;
  style?: React.CSSProperties;
}

// ── Time helper ───────────────────────────────────────────────────────
function relativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Component ─────────────────────────────────────────────────────────
export function MessageBubble({ role, content, thinkingContent, timestamp, isStreaming, style }: MessageBubbleProps) {
  const [thoughtExpanded, setThoughtExpanded] = useState(false);
  const [autoExpanded, setAutoExpanded] = useState(false);
  const hasThinking = !!thinkingContent;

  // Auto-expand ONCE when thinking first arrives — no deps on thinkingContent
  // so subsequent tokens don't override user's manual collapse.
  useEffect(() => {
    if (isStreaming && hasThinking && !autoExpanded) {
      setThoughtExpanded(true);
      setAutoExpanded(true);
    }
  }, [isStreaming, hasThinking, autoExpanded]);

  const isThinking = hasThinking && isStreaming && !content;
  const thoughtLabel = isThinking ? "Thinking" : hasThinking ? "Thought" : "";

  return (
    <div
      style={style}
      className={cn(
        "flex flex-col",
        role === "user" ? "items-end" : "items-start",
        "animate-fade-in",
        "motion-safe:[animation-delay:calc(var(--i,0)*30ms)]",
      )}
      role="article"
      aria-label={`${role} message`}
    >
      {role === "assistant" ? (
        <>
          {/* Thinking — collapsible + scrollable */}
          {hasThinking && (
            <div className="max-w-[85%] mb-1.5 w-full min-w-0">
              {/* Toggle header */}
              <button
                type="button"
                onClick={() => setThoughtExpanded((prev) => !prev)}
                className={cn(
                  "flex items-center gap-1.5 w-full rounded-lg border px-3 py-1.5",
                  "border-accent-cyan/8 bg-bg-elevated/50",
                  "text-[10px] font-medium text-accent-cyan/70 tracking-wide uppercase",
                  "hover:bg-bg-surface/60 motion-safe:transition-colors motion-safe:duration-150",
                  "cursor-pointer select-none",
                )}
                aria-expanded={thoughtExpanded}
                aria-label={thoughtExpanded ? "Collapse thought" : "Expand thought"}
              >
                <ChevronDown
                  className={cn(
                    "shrink-0 motion-safe:transition-transform motion-safe:duration-200",
                    thoughtExpanded ? "rotate-0" : "-rotate-90",
                  )}
                />
                {thoughtLabel}
                <span className="ml-auto text-[9px] text-text-muted font-normal normal-case">
                  {thoughtExpanded ? "hide" : "show"}
                </span>
              </button>

              {/* Expandable content */}
              <div
                className={cn(
                  "overflow-hidden motion-safe:transition-all motion-safe:duration-300 motion-safe:ease-out",
                  thoughtExpanded ? "max-h-96 opacity-100 mt-1" : "max-h-0 opacity-0 mt-0",
                )}
              >
                <div
                  className={cn(
                    "rounded-lg border px-3 py-2 overflow-y-auto",
                    "border-accent-cyan/8 bg-bg-elevated/50",
                    "text-[12px] leading-relaxed text-text-muted",
                    "font-mono whitespace-pre-wrap",
                    "max-h-60",
                    "shadow-[inset_0_1px_0_rgba(255,255,255,0.04),inset_0_-1px_0_rgba(0,0,0,0.1)]",
                    "scrollbar-thin",
                  )}
                >
                  {thinkingContent}
                </div>
              </div>
            </div>
          )}

          {/* Content — streams token by token */}
          <div
            className={cn(
              "max-w-[85%] rounded-xl px-4 py-2.5",
              "bg-bg-glass backdrop-blur-xl text-text-primary",
              "border border-border-subtle border-l-2 border-l-accent-cyan",
            )}
          >
            {content ? (
              <MarkdownRenderer content={content} isStreaming={isStreaming} />
            ) : isThinking ? null : (
              <span className="text-sm text-text-muted italic">Thinking…</span>
            )}
          </div>
        </>
      ) : (
        <>
          <div
            className={cn(
              "max-w-[85%] rounded-xl px-4 py-2.5",
              "bg-accent-red-muted/20 text-text-primary",
              "border border-accent-red/10",
            )}
          >
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
          </div>
        </>
      )}

      {/* Timestamp */}
      {timestamp && (
        <span className="text-[10px] text-text-muted font-mono mt-1 px-1" title={new Date(timestamp).toLocaleString()}>
          {relativeTime(timestamp)}
        </span>
      )}
    </div>
  );
}
