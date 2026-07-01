"use client";

import { useEffect, useState } from "react";
import { cn } from "@/shared/lib/utils";
import type { Conversation } from "../api";

// ── Props ─────────────────────────────────────────────────────────────
interface ConversationSidebarProps {
  open: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
  onRename: (id: number, title: string) => void;
  onNewChat: () => void;
  error: string | null;
  onClearError: () => void;
}

// ── Component ─────────────────────────────────────────────────────────
export function ConversationSidebar({
  open,
  onClose,
  conversations,
  activeId,
  onSelect,
  onDelete,
  onRename,
  onNewChat,
  error,
  onClearError,
}: ConversationSidebarProps) {
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");

  // Close on Escape
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Filter conversations by search
  const q = search.toLowerCase();
  const filtered = q
    ? conversations.filter((c) => c.title.toLowerCase().includes(q))
    : conversations;

  // Group by date
  const groups = groupByDate(filtered);

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          "fixed left-0 top-0 z-40 h-dvh w-[320px] sm:w-[360px]",
          "border-r border-border-default",
          "bg-bg-glass backdrop-blur-2xl",
          "flex flex-col",
          "motion-safe:transition-transform motion-safe:duration-300 motion-safe:ease-out",
          open ? "translate-x-0" : "-translate-x-full",
        )}
        role="dialog"
        aria-label="Conversations"
      >
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-border-subtle px-4 py-3">
          <h2 className="text-sm font-semibold text-text-primary flex-1">Conversations</h2>
          <button
            onClick={onNewChat}
            className={cn(
              "flex items-center justify-center h-7 w-7 rounded-lg",
              "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
            aria-label="New conversation"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M8 2v12M2 8h12" />
            </svg>
          </button>
          <button
            onClick={onClose}
            className={cn(
              "flex items-center justify-center h-7 w-7 rounded-lg",
              "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
            aria-label="Close sidebar"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M12 4L4 12M4 4l8 8" />
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="px-3 py-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations…"
            className={cn(
              "w-full rounded-lg border border-border-subtle bg-bg-surface px-3 py-1.5",
              "text-sm text-text-primary placeholder:text-text-muted",
              "outline-none focus:border-accent-red/50 focus:ring-1 focus:ring-accent-red/25",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mx-3 mb-2 rounded-lg border border-accent-red/20 bg-accent-red/5 px-3 py-2 text-xs text-accent-red">
            {error}
            <button onClick={onClearError} className="ml-1 font-medium underline hover:text-accent-red/80">Dismiss</button>
          </div>
        )}

        {/* List */}
        <div className="flex-1 overflow-y-auto overscroll-contain px-2 py-1">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-sm text-text-muted">{search ? "No matches" : "No conversations yet"}</p>
              {!search && (
                <button onClick={onNewChat} className="mt-2 text-xs text-accent-red hover:text-accent-red/80 font-medium">
                  Start one
                </button>
              )}
            </div>
          ) : (
            Object.entries(groups).map(([dateLabel, convs]) => (
              <div key={dateLabel}>
                <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
                  {dateLabel}
                </div>
                {convs.map((conv) => {
                  const isActive = conv.id === activeId;
                  const isEditing = editingId === conv.id;
                  return (
                    <div key={conv.id} className="group relative">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onBlur={() => { onRename(conv.id, editTitle || conv.title); setEditingId(null); }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") { onRename(conv.id, editTitle || conv.title); setEditingId(null); }
                            if (e.key === "Escape") setEditingId(null);
                          }}
                          className={cn(
                            "w-full rounded-lg border border-accent-red/50 bg-bg-surface px-3 py-2",
                            "text-sm text-text-primary outline-none focus-visible:outline-2 focus-visible:outline-border-input-focus",
                          )}
                          autoFocus
                        />
                      ) : (
                        <button
                          onClick={() => onSelect(conv.id)}
                          className={cn(
                            "w-full rounded-lg px-3 py-2 text-left",
                            "motion-safe:transition-colors motion-safe:duration-100",
                            isActive
                              ? "bg-accent-red-muted/30 text-accent-red"
                              : "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
                          )}
                        >
                          <p className="text-sm font-medium truncate leading-tight">{conv.title || "Untitled"}</p>
                          <p className="text-xs text-text-muted mt-0.5">{conv.message_count} messages</p>
                        </button>
                      )}

                      {/* Hover actions */}
                      {!isEditing && (
                        <div className={cn(
                          "absolute right-1 top-1/2 -translate-y-1/2",
                          "flex items-center gap-0.5",
                          "opacity-0 group-hover:opacity-100",
                          "motion-safe:transition-opacity motion-safe:duration-100",
                        )}>
                          <button
                            onClick={(e) => { e.stopPropagation(); setEditingId(conv.id); setEditTitle(conv.title); }}
                            className="flex h-6 w-6 items-center justify-center rounded text-text-muted hover:text-text-primary hover:bg-bg-hover"
                            aria-label="Rename"
                          >
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                              <path d="M12.5 1.5l2 2L5 13H3v-2l9.5-9.5z" />
                            </svg>
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                            className="flex h-6 w-6 items-center justify-center rounded text-text-muted hover:text-accent-red hover:bg-accent-red/10"
                            aria-label="Delete"
                          >
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                              <path d="M2 4h12M5 4V2h6v2M4 4l1 10h6l1-10" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}

// ── Date grouping helper ──────────────────────────────────────────────
function groupByDate(convs: Conversation[]): Record<string, Conversation[]> {
  const groups: Record<string, Conversation[]> = {};
  const now = new Date();
  const today = toDateStr(now);
  const yesterday = toDateStr(new Date(now.getTime() - 86400000));

  for (const conv of convs) {
    const d = toDateStr(new Date(conv.created_at));
    const label = d === today ? "Today" : d === yesterday ? "Yesterday" : d;
    if (!groups[label]) groups[label] = [];
    groups[label].push(conv);
  }
  return groups;
}

function toDateStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
