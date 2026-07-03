"use client";

import { useState } from "react";
import { cn } from "@/shared/lib/utils";
import { MarkdownRenderer } from "./MarkdownRenderer";

// ── Props ─────────────────────────────────────────────────────────────
interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  thinkingContent?: string;
  timestamp?: string;
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
export function MessageBubble({ role, content, thinkingContent, timestamp, style }: MessageBubbleProps) {
  const isStreaming = !content && !!thinkingContent;

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
          {/* Thinking — always visible, streams inline */}
          {thinkingContent && (
            <div className="max-w-[85%] mb-1.5">
              <div
                className={cn(
                  "rounded-lg border px-3 py-2",
                  "border-accent-cyan/8 bg-bg-elevated/50",
                  "text-[12px] leading-relaxed text-text-muted",
                  "font-mono whitespace-pre-wrap",
                  "shadow-[inset_0_1px_0_rgba(255,255,255,0.04),inset_0_-1px_0_rgba(0,0,0,0.1)]",
                )}
              >
                <span className="block text-[10px] font-medium text-accent-cyan/70 tracking-wide uppercase mb-1">
                  Thought
                </span>
                {thinkingContent}
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
              <MarkdownRenderer content={content} />
            ) : (
              <span className="text-sm text-text-muted italic">
                {thinkingContent ? "Writing…" : "Thinking…"}
              </span>
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
