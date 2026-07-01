"use client";

import { useMemo, useState } from "react";
import { cn } from "@/shared/lib/utils";
import { CodeBlock } from "./CodeBlock";

// ── Props ─────────────────────────────────────────────────────────────
interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
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

// ── Content parser ────────────────────────────────────────────────────
function parseContent(content: string): Array<{ type: "text" | "code"; content: string; language?: string }> {
  const parts: Array<{ type: "text" | "code"; content: string; language?: string }> = [];
  const regex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;
  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "code", language: match[1] || undefined, content: match[2].trim() });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < content.length) {
    parts.push({ type: "text", content: content.slice(lastIndex) });
  }
  if (parts.length === 0) parts.push({ type: "text", content });
  return parts;
}

// ── Component ─────────────────────────────────────────────────────────
export function MessageBubble({ role, content, timestamp }: MessageBubbleProps) {
  const parts = useMemo(() => parseContent(content), [content]);

  return (
    <div
      className={cn(
        "flex flex-col",
        role === "user" ? "items-end" : "items-start",
        "animate-fade-in motion-safe:animate-fade-in",
      )}
      role="article"
      aria-label={`${role} message`}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-xl px-4 py-2.5",
          role === "user"
            ? [
                "bg-accent-red-muted/20 text-text-primary",
                "border border-accent-red/10",
              ]
            : [
                "bg-bg-glass backdrop-blur-xl text-text-primary",
                "border border-border-subtle",
                "border-l-2 border-l-accent-cyan",
              ],
        )}
      >
        {parts.map((part, i) => {
          if (part.type === "code") {
            return <CodeBlock key={i} language={part.language}>{part.content}</CodeBlock>;
          }
          return part.content.split("\n\n").filter(Boolean).map((para, j) => (
            <p key={`${i}-${j}`} className="text-sm leading-relaxed whitespace-pre-wrap">{para}</p>
          ));
        })}
      </div>

      {/* Timestamp */}
      {timestamp && (
        <span className="text-[10px] text-text-muted font-mono mt-1 px-1" title={new Date(timestamp).toLocaleString()}>
          {relativeTime(timestamp)}
        </span>
      )}
    </div>
  );
}
