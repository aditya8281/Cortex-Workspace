"use client";

import { useState, useRef, useCallback } from "react";
import { Button } from "@/shared/ui/Button";

interface ChatInputProps {
  onSend: (content: string) => void;
  onTyping?: () => void;
  disabled?: boolean;
  model?: string;
}

export function ChatInput({ onSend, onTyping, disabled, model }: ChatInputProps) {
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
    <div className="border-t border-border-subtle bg-void p-4">
      <div className="flex items-end gap-2">
        <div className="flex-1 rounded-xl border border-border-default bg-bg-surface focus-within:border-accent/50 transition-colors duration-150">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => { setValue(e.target.value); onTyping?.(); }}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Type a message…"
            disabled={disabled}
            rows={1}
            className="w-full resize-none bg-transparent px-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
          />
        </div>
        <Button
          onClick={handleSubmit}
          disabled={!value.trim() || disabled}
          size="md"
          className="flex-shrink-0"
        >
          Send
        </Button>
      </div>
      {model && (
        <p className="mt-2 text-xs text-text-muted font-mono">
          Model: {model}
        </p>
      )}
    </div>
  );
}
