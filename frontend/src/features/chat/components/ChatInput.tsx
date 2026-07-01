"use client";

import { useState, useRef, useCallback } from "react";
import { cn } from "@/shared/lib/utils";
import { PaperclipIcon, MicIcon, SendIcon } from "@/shared/ui/icons";

interface ChatInputProps {
  onSend: (content: string) => void;
  onTyping?: () => void;
  disabled?: boolean;
  onStop?: () => void;
}

export function ChatInput({ onSend, onTyping, disabled, onStop }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const handleInput = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  }, []);

  return (
    <div className="border-t border-border-subtle px-4 sm:px-6 py-3">
      <div className={cn(
        "mx-auto max-w-3xl flex items-end gap-2",
        "rounded-xl border border-border-subtle",
        "bg-bg-glass backdrop-blur-xl",
        "px-3 py-2",
        "motion-safe:transition-colors motion-safe:duration-200",
        "focus-within:border-border-default",
      )}>
        {/* Attach button */}
        <button
          type="button"
          className="flex-shrink-0 flex items-center justify-center h-8 w-8 rounded-lg text-text-muted hover:text-text-secondary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
          aria-label="Attach file"
          tabIndex={-1}
          title="Attach (coming soon)"
        >
          <PaperclipIcon size={16} />
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); onTyping?.(); }}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask Cortex anything…"
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none max-h-[200px]"
        />

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Voice button (future) */}
          <button
            type="button"
            className="flex items-center justify-center h-8 w-8 rounded-lg text-text-muted hover:text-text-secondary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
            aria-label="Voice input"
            tabIndex={-1}
            title="Voice (coming soon)"
          >
            <MicIcon size={16} />
          </button>

          {/* Send / Stop */}
          {disabled ? (
            <button
              type="button"
              onClick={onStop}
              className={cn(
                "flex items-center justify-center h-8 w-8 rounded-lg",
                "bg-accent-red text-white",
                "hover:bg-accent-red/90",
                "motion-safe:transition-colors motion-safe:duration-150",
              )}
              aria-label="Stop generation"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <rect x="3" y="3" width="10" height="10" rx="1" />
              </svg>
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!value.trim()}
              className={cn(
                "flex items-center justify-center h-8 w-8 rounded-lg",
                "bg-accent-red text-white",
                "hover:bg-accent-red/90",
                "disabled:opacity-30 disabled:cursor-not-allowed",
                "motion-safe:transition-colors motion-safe:duration-150",
              )}
              aria-label="Send message"
            >
              <SendIcon size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
