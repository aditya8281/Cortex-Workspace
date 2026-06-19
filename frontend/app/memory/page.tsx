"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiListMemory, apiCreateMemory } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";
import { cn } from "../../src/lib/utils";
import { staggerContainer, staggerItem, scaleIn } from "../../src/lib/motion";
import { Brain, Plus, X, Hash, Calendar, FolderOpen, Loader2 } from "lucide-react";
import type { MemoryEntry, MemoryListResponse } from "../../src/shared/types";

const CATEGORIES = ["all", "note", "repository", "embedding", "index", "system"] as const;

export default function MemoryPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [categories, setCategories] = useState<Record<string, number>>({});
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 24;

  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState("note");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  const fetchEntries = useCallback(async (cat: string, off: number, append = false) => {
    setLoading(true);
    setError("");
    try {
      const params: { limit: number; offset: number } = { limit, offset: off };
      const data: MemoryListResponse = await apiListMemory(params);
      if (append) {
        setEntries((prev) => [...prev, ...data.entries]);
      } else {
        setEntries(data.entries);
      }
      setCategories(data.categories);
      setTotalCount(data.count);
      setHasMore(off + data.entries.length < data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load memory entries");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    if (user) fetchEntries(activeCategory, 0);
  }, [user, activeCategory, fetchEntries]);

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    setOffset(0);
  };

  const handleLoadMore = () => {
    const newOffset = offset + limit;
    setOffset(newOffset);
    fetchEntries(activeCategory, newOffset, true);
  };

  const handleCreate = async () => {
    if (!newTitle.trim() || !newContent.trim()) {
      setCreateError("Title and content are required");
      return;
    }
    setCreateLoading(true);
    setCreateError("");
    setCreateSuccess(false);
    try {
      await apiCreateMemory({
        title: newTitle.trim(),
        content: newContent.trim(),
        category: newCategory,
      });
      setNewTitle("");
      setNewContent("");
      setNewCategory("note");
      setCreateSuccess(true);
      setShowCreate(false);
      fetchEntries(activeCategory, 0);
      setTimeout(() => setCreateSuccess(false), 3000);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create entry");
    } finally {
      setCreateLoading(false);
    }
  };

  const filteredEntries = activeCategory === "all"
    ? entries
    : entries.filter((e) => e.category === activeCategory);

  if (authLoading || !user) return null;

  return (
    <DashboardShell>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
        <div className="page-header flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-text">Memory</h1>
            <p className="text-sm text-text-muted mt-1">
              Knowledge base with {totalCount} entr{totalCount === 1 ? "y" : "ies"}
            </p>
          </div>
          <Button onClick={() => setShowCreate(!showCreate)}>
            {showCreate ? (
              <>
                <X className="h-4 w-4" />
                Cancel
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" />
                New Entry
              </>
            )}
          </Button>
        </div>

        <AnimatePresence>
          {showCreate && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
            >
              <Card className="p-5">
                <h2 className="text-sm font-medium text-text mb-4">Create Knowledge Entry</h2>
                <div className="grid gap-3">
                  <Input
                    label="Title"
                    placeholder="Entry title"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    required
                  />
                  <div className="grid gap-1.5">
                    <label className="text-xs font-medium text-text-secondary">Category</label>
                    <div className="flex gap-2 flex-wrap">
                      {["note", "repository", "embedding", "index", "system"].map((cat) => (
                        <button
                          key={cat}
                          type="button"
                          onClick={() => setNewCategory(cat)}
                          className={cn(
                            "px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                            newCategory === cat
                              ? "bg-accent text-bg shadow-glow"
                              : "bg-bg-surface border border-border text-text-secondary hover:bg-bg-hover hover:text-text"
                          )}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="grid gap-1.5">
                    <label className="text-xs font-medium text-text-secondary">Content</label>
                    <textarea
                      value={newContent}
                      onChange={(e) => setNewContent(e.target.value)}
                      placeholder="Write your knowledge entry content here..."
                      rows={6}
                      className="w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 resize-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 focus:shadow-glow"
                      required
                    />
                  </div>
                  {createError && (
                    <p className="text-sm text-error bg-error/10 rounded-md px-3 py-2 border border-error/10">{createError}</p>
                  )}
                  <div className="flex justify-end">
                    <Button loading={createLoading} onClick={handleCreate}>
                      Create Entry
                    </Button>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {createSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl bg-success/10 border border-success/10 px-4 py-2 text-sm text-success font-medium"
          >
            Entry created successfully.
          </motion.div>
        )}

        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => handleCategoryChange(cat)}
              className={cn(
                "relative px-4 py-1.5 rounded-full text-xs font-medium transition-all",
                activeCategory === cat
                  ? "text-bg"
                  : "bg-bg-surface border border-border text-text-secondary hover:bg-bg-hover hover:text-text"
              )}
            >
              {activeCategory === cat && (
                <motion.div
                  layoutId="memory-category-indicator"
                  className="absolute inset-0 rounded-full bg-accent shadow-glow"
                  transition={{ type: "spring", damping: 25, stiffness: 300 }}
                />
              )}
              <span className="relative z-10">
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
                {cat !== "all" && categories[cat] ? (
                  <span className="ml-1.5 text-[11px] opacity-70">({categories[cat]})</span>
                ) : null}
              </span>
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-xl bg-error/10 border border-error/10 px-4 py-2 text-sm text-error">
            {error}
          </div>
        )}

        {loading && entries.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 text-accent animate-spin" />
              <p className="text-sm text-text-muted">Loading memory entries...</p>
            </div>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="h-12 w-12 rounded-xl bg-bg-surface border border-border-subtle flex items-center justify-center mb-3">
              <Brain className="h-6 w-6 text-text-muted" />
            </div>
            <p className="text-sm font-medium text-text-secondary">No memory entries found</p>
            <p className="text-xs text-text-muted mt-1">Create your first knowledge entry to get started.</p>
          </div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="space-y-3"
          >
            {filteredEntries.map((entry, i) => (
              <motion.div key={entry.id} variants={staggerItem} custom={i}>
                <Card hover className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <h3 className="text-sm font-medium text-text truncate">{entry.title}</h3>
                        <span className="shrink-0 px-2 py-0.5 rounded-full text-[11px] font-medium bg-accent-faint text-accent border border-accent/10">
                          {entry.category}
                        </span>
                      </div>
                      <p className="text-sm text-text-muted line-clamp-2 mb-2.5">{entry.content}</p>
                      <div className="flex items-center gap-3 text-xs text-text-muted">
                        <span className="flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          {entry.id}
                        </span>
                        {entry.source_path && (
                          <span className="flex items-center gap-1 font-mono truncate max-w-[200px]" title={entry.source_path}>
                            <FolderOpen className="h-3 w-3 shrink-0" />
                            {entry.source_path}
                          </span>
                        )}
                        {entry.created_at && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {new Date(entry.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}

        {hasMore && !loading && filteredEntries.length > 0 && (
          <div className="flex justify-center">
            <Button variant="secondary" onClick={handleLoadMore}>
              Load more
            </Button>
          </div>
        )}

        {loading && entries.length > 0 && (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 text-accent animate-spin" />
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
