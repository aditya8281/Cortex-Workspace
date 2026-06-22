"use client";

import { useState, type ReactNode } from "react";
import Modal from "../../src/shared/ui/Modal";
import Button from "../../src/shared/ui/Button";
import { apiCreateMemory, apiUpdateMemory } from "../../src/shared/auth/cortexApi";

interface MemoryEditorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
  entry?: {
    id: number;
    title: string;
    content: string;
    category: string;
    source_path: string | null;
    tags: string[];
  } | null;
}

export default function MemoryEditor({ open, onOpenChange, onSaved, entry }: MemoryEditorProps) {
  const isEditing = !!entry;
  const [title, setTitle] = useState(entry?.title ?? "");
  const [content, setContent] = useState(entry?.content ?? "");
  const [category, setCategory] = useState(entry?.category ?? "general");

  const CATEGORIES = ["code", "document", "note", "idea", "project", "general"];
  const [sourcePath, setSourcePath] = useState(entry?.source_path ?? "");
  const [tagsText, setTagsText] = useState(entry?.tags?.join(", ") ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    if (!entry) {
      setTitle("");
      setContent("");
      setCategory("general");
      setSourcePath("");
      setTagsText("");
    }
    setError(null);
  }

  async function handleSave() {
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    if (!content.trim()) {
      setError("Content is required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const tags = tagsText
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      const payload = {
        title: title.trim(),
        content: content.trim(),
        category: category.trim() || "general",
        source_path: sourcePath.trim() || undefined,
        tags: tags.length > 0 ? tags : undefined,
      };
      if (isEditing && entry) {
        await apiUpdateMemory(entry.id, payload);
      } else {
        await apiCreateMemory(payload);
      }
      onSaved();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save memory");
    } finally {
      setSaving(false);
    }
  }

  const labelClass = "text-xs font-medium text-text-secondary";
  const inputClass =
    "w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10 focus:shadow-glow";

  return (
    <Modal open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }} title={isEditing ? "Edit Memory" : "New Memory"}>
      <div className="grid gap-3.5">
        <div>
          <label className={labelClass}>Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Memory title"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your memory..."
            rows={5}
            className={`${inputClass} resize-y min-h-[100px]`}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={inputClass}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Source path (optional)</label>
            <input
              type="text"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="/path/to/file"
              className={inputClass}
            />
          </div>
        </div>
        <div>
          <label className={labelClass}>Tags (comma-separated)</label>
          <input
            type="text"
            value={tagsText}
            onChange={(e) => setTagsText(e.target.value)}
            placeholder="ai, cortex, memory"
            className={inputClass}
          />
        </div>
        {error && <p className="text-xs text-error">{error}</p>}
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button loading={saving} onClick={handleSave}>
            {isEditing ? "Save Changes" : "Create Memory"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
