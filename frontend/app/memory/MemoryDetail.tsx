"use client";

import { useState } from "react";
import Modal from "../../src/shared/ui/Modal";
import Button from "../../src/shared/ui/Button";
import Badge from "../../src/shared/ui/Badge";
import type { MemoryEntry } from "../../src/shared/types";
import { apiDeleteMemory } from "../../src/shared/auth/cortexApi";

interface MemoryDetailProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entry: MemoryEntry | null;
  onEdit: (entry: MemoryEntry) => void;
  onDeleted: () => void;
}

export default function MemoryDetail({ open, onOpenChange, entry, onEdit, onDeleted }: MemoryDetailProps) {
  const [deleting, setDeleting] = useState(false);

  if (!entry) return null;

  async function handleDelete() {
    if (!entry) return;
    if (!window.confirm("Delete this memory?")) return;
    setDeleting(true);
    try {
      await apiDeleteMemory(entry.id);
      onDeleted();
      onOpenChange(false);
    } catch {
      // silently fail
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title={entry.title}>
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2 items-center">
          <Badge variant="accent">{entry.category}</Badge>
          {entry.tags?.map((tag) => (
            <Badge key={tag}>{tag}</Badge>
          ))}
          {entry.embedding_id && (
            <Badge variant="success">embedded</Badge>
          )}
        </div>

        {entry.source_path && (
          <p className="text-xs font-mono text-text-muted">
            {entry.source_path}
          </p>
        )}

        <div className="rounded-xl bg-bg-surface border border-border-subtle p-4">
          <p className="text-sm text-text whitespace-pre-wrap leading-relaxed">
            {entry.content}
          </p>
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono text-text-muted">
          {entry.created_at && (
            <span>Created: {new Date(entry.created_at).toLocaleString()}</span>
          )}
          {entry.updated_at && entry.updated_at !== entry.created_at && (
            <span>Updated: {new Date(entry.updated_at).toLocaleString()}</span>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-border-subtle pt-4">
          <Button variant="danger" loading={deleting} onClick={handleDelete}>
            Delete
          </Button>
          <Button variant="secondary" onClick={() => onEdit(entry)}>
            Edit
          </Button>
        </div>
      </div>
    </Modal>
  );
}
