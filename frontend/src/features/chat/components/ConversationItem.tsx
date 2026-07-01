"use client";

import { useState, useRef, useEffect } from "react";

interface ConversationItemProps {
  id: string;
  title: string;
  isActive: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

export function ConversationItem({
  id,
  title,
  isActive,
  onSelect,
  onRename,
  onDelete,
}: ConversationItemProps) {
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(title);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const handleSave = () => {
    if (editTitle.trim()) onRename(id, editTitle.trim());
    else setEditTitle(title);
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") {
      setEditTitle(title);
      setEditing(false);
    }
  };

  return (
    <div
      className={`group flex items-center justify-between gap-2 px-3 py-2 rounded-lg cursor-pointer motion-safe:transition-colors motion-safe:duration-150 ${
        isActive
          ? "bg-bg-hover text-text-primary"
          : "text-text-secondary hover:bg-bg-hover/50"
      }`}
      onClick={() => !editing && onSelect(id)}
    >
      {editing ? (
        <input
          ref={inputRef}
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-bg-surface border border-border-default rounded px-2 py-0.5 text-xs text-text-primary focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="flex-1 truncate text-xs">{title}</span>
      )}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 motion-safe:transition-opacity motion-safe:duration-150 flex-shrink-0">
        {!editing && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setEditing(true);
              }}
              className="p-0.5 text-text-muted hover:text-text-secondary cursor-pointer"
              aria-label="Rename conversation"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.2"
              >
                <path d="M10 1.5l2.5 2.5L4.5 12H2v-2.5L10 1.5z" />
              </svg>
            </button>
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDeleteConfirm(!showDeleteConfirm);
                }}
                className="p-0.5 text-text-muted hover:text-danger cursor-pointer"
                aria-label="Delete conversation"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.2"
                >
                  <path d="M2 3.5h10M5 3.5V2.5a1 1 0 011-1h2a1 1 0 011 1v1M3.5 3.5l.5 8a1 1 0 001 1h4a1 1 0 001-1l.5-8" />
                </svg>
              </button>
              {showDeleteConfirm && (
                <div
                  className="absolute right-0 top-full mt-1 z-10 bg-bg-elevated border border-border-subtle rounded-lg p-2 shadow-lg"
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="text-[10px] text-text-muted mb-1.5">
                    Delete this?
                  </p>
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => {
                        onDelete(id);
                        setShowDeleteConfirm(false);
                      }}
                      className="text-[10px] text-danger hover:underline cursor-pointer"
                    >
                      Yes
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="text-[10px] text-text-muted hover:underline cursor-pointer"
                    >
                      No
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
