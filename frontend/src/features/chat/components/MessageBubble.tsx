"use client";

import { cn } from "@/shared/lib/utils";
import type { ChatMessage } from "../api";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full animate-fade-in",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-xl px-4 py-3 text-sm",
          isUser
            ? "bg-accent/15 text-text-primary rounded-br-md"
            : "bg-bg-elevated text-text-primary rounded-bl-md",
        )}
      >
        <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
        <div className="mt-1.5 flex items-center gap-2">
          <span className="text-[0.625rem] text-text-muted font-mono">
            {message.tokens} tokens
          </span>
        </div>
      </div>
    </div>
  );
}
