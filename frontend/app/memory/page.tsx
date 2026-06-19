"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Brain, Search, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Button from "../../src/shared/ui/Button";
import PageTransition from "../../src/shared/ui/PageTransition";
import type { MemoryEntry, MemorySearchResult } from "../../src/shared/types";
import {
  apiListMemory,
  apiSearchMemory,
} from "../../src/shared/auth/cortexApi";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { cn } from "../../src/lib/utils";
import MemorySearch from "./MemorySearch";
import MemoryEditor from "./MemoryEditor";
import MemoryDetail from "./MemoryDetail";

type ViewMode = "list" | "search";

export default function MemoryPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [categories, setCategories] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const [query, setQuery] = useState("");
  const [semantic, setSemantic] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [searchResults, setSearchResults] = useState<MemorySearchResult[]>([]);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<MemoryEntry | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailEntry, setDetailEntry] = useState<MemoryEntry | null>(null);

  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [authLoading, user, router]);

  const fetchList = useCallback(async (reset = false) => {
    setLoading(true);
    setError(null);
    try {
      const newOffset = reset ? 0 : offset;
      const data = await apiListMemory({ limit, offset: newOffset, category: selectedCategory ?? undefined });
      if (reset) {
        setEntries(data.entries);
      } else {
        setEntries((prev) => [...prev, ...data.entries]);
      }
      setCategories(data.categories || {});
      setTotal(data.total ?? 0);
      setOffset(newOffset + data.entries.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load memories");
    } finally {
      setLoading(false);
    }
  }, [offset, selectedCategory]);

  const initialised = useRef(false);
  useEffect(() => {
    if (initialised.current) return;
    initialised.current = true;
    apiListMemory({ limit, offset: 0 })
      .then((data) => {
        setEntries(data.entries);
        setCategories(data.categories || {});
        setTotal(data.total ?? 0);
        setOffset(data.entries.length);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load memories");
      })
      .finally(() => setLoading(false));
  }, []);

  const catFilterInit = useRef(false);
  useEffect(() => {
    if (!catFilterInit.current) { catFilterInit.current = true; return; }
    setLoading(true);
    apiListMemory({ limit, offset: 0, category: selectedCategory ?? undefined })
      .then((data) => {
        setEntries(data.entries);
        setCategories(data.categories || {});
        setTotal(data.total ?? 0);
        setOffset(data.entries.length);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load memories");
      })
      .finally(() => setLoading(false));
  }, [selectedCategory]);

  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function triggerSearch(searchQuery: string) {
    if (!searchQuery.trim()) {
      setViewMode("list");
      return;
    }
    setViewMode("search");
    try {
      const data = await apiSearchMemory({ query: searchQuery.trim() });
      setSearchResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  }

  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    if (query.trim()) {
      searchTimerRef.current = setTimeout(() => triggerSearch(query), 300);
    }
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    };
  }, [query]);

  function openNewEditor() {
    setEditingEntry(null);
    setEditorOpen(true);
  }

  function openEditEditor(entry: MemoryEntry) {
    setDetailOpen(false);
    setEditingEntry(entry);
    setEditorOpen(true);
  }

  function openDetail(entry: MemoryEntry | MemorySearchResult) {
    setDetailEntry(entry as MemoryEntry);
    setDetailOpen(true);
  }

  function handleSaved() {
    fetchList(true);
  }

  function handleDeleted() {
    fetchList(true);
  }

  const displayEntries = viewMode === "search" ? searchResults : entries;
  const hasMore = entries.length < total;

  const categoryColors: Record<string, string> = {
    code: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    document: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    note: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    default: "bg-accent/10 text-accent border-accent/20",
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text flex items-center gap-2">
              <Brain className="h-6 w-6 text-accent" />
              Memory
            </h1>
            <p className="mt-1 text-sm text-text-muted">
              {total} {total === 1 ? "memory" : "memories"} stored
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-elevated border border-border-subtle">
              <RefreshCw className="h-3 w-3 text-text-muted" />
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">Auto-sync</span>
              <span className="h-1.5 w-1.5 rounded-full bg-success shadow-[0_0_6px_rgba(34,197,94,0.4)]" />
            </div>
            <Button onClick={openNewEditor}>
              <Plus className="h-4 w-4" />
              New Memory
            </Button>
          </div>
        </div>

        <div className="mb-6">
          <MemorySearch
            query={query}
            onQueryChange={setQuery}
            semantic={semantic}
            onSemanticChange={setSemantic}
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
            {error}
          </div>
        )}

        <div className="flex gap-6 min-h-[400px]">
          <div className="flex-1 min-w-0">
            {Object.keys(categories).length > 0 && (
              <div className="mb-4 flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
                    !selectedCategory
                      ? "bg-accent/10 text-accent border-accent/20"
                      : "bg-bg-elevated text-text-muted border-border-subtle hover:border-border"
                  )}
                >
                  All ({total})
                </button>
                {Object.entries(categories).map(([cat, count]) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                    className={cn(
                      "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
                      selectedCategory === cat
                        ? "bg-accent/10 text-accent border-accent/20"
                        : "bg-bg-elevated text-text-muted border-border-subtle hover:border-border"
                    )}
                  >
                    {cat} ({count})
                  </button>
                ))}
              </div>
            )}

            {loading && entries.length === 0 ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-24 animate-pulse rounded-xl bg-bg-elevated border border-border-subtle" />
                ))}
              </div>
            ) : displayEntries.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <motion.div
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  <Brain className="h-16 w-16 text-accent/30 mb-4" />
                </motion.div>
                <p className="text-sm font-medium text-text mb-1">
                  {viewMode === "search" ? "No results found" : "Build your neural knowledge base"}
                </p>
                <p className="text-xs text-text-muted max-w-xs">
                  {viewMode === "search"
                    ? "Try a different search query or adjust filters."
                    : "Start adding memories to build your persistent knowledge graph."}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <AnimatePresence mode="popLayout">
                  {displayEntries.map((entry) => (
                    <motion.button
                      key={entry.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      onClick={() => openDetail(entry)}
                      className={cn(
                        "w-full rounded-xl border p-4 text-left transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.995]",
                        detailEntry?.id === entry.id
                          ? "border-accent/30 bg-accent-faint shadow-glow"
                          : "border-border-subtle bg-bg-elevated hover:border-border-accent hover:shadow-glow"
                      )}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <h3 className="text-sm font-semibold text-text truncate">{entry.title}</h3>
                          <p className="mt-1 text-xs text-text-muted line-clamp-2">{entry.content}</p>
                        </div>
                        <div className="flex flex-col items-end gap-1 shrink-0">
                          <span className={cn(
                            "rounded-full px-2 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider border",
                            categoryColors[entry.category] || categoryColors.default
                          )}>
                            {entry.category}
                          </span>
                          {(entry as MemorySearchResult).score !== undefined && (
                            <span className="text-[10px] font-mono text-text-muted">
                              {((entry as MemorySearchResult).score * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                      {entry.tags && entry.tags.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {entry.tags.map((tag) => (
                            <span key={tag} className="rounded-full bg-bg-surface px-2 py-0.5 text-[10px] font-mono text-text-muted border border-border-subtle">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </motion.button>
                  ))}
                </AnimatePresence>
              </div>
            )}

            {viewMode === "list" && hasMore && (
              <div className="mt-6 flex justify-center">
                <Button variant="secondary" loading={loading} onClick={() => fetchList()}>
                  Load More
                </Button>
              </div>
            )}
          </div>

          <div className="hidden lg:block w-96 shrink-0">
            <div className="sticky top-24">
              <AnimatePresence mode="wait">
                {detailEntry ? (
                  <motion.div
                    key={detailEntry.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                    className="rounded-xl border border-border-subtle bg-bg-elevated p-5"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider border",
                        categoryColors[detailEntry.category] || categoryColors.default
                      )}>
                        {detailEntry.category}
                      </span>
                      <div className="flex gap-2">
                        <button onClick={() => openEditEditor(detailEntry)} className="text-xs text-text-muted hover:text-accent transition-colors">Edit</button>
                        <button onClick={() => setDetailEntry(null)} className="text-xs text-text-muted hover:text-text transition-colors">Close</button>
                      </div>
                    </div>
                    <h3 className="text-lg font-semibold text-text mb-2">{detailEntry.title}</h3>
                    <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">{detailEntry.content}</p>
                    {detailEntry.tags && detailEntry.tags.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-1">
                        {detailEntry.tags.map((tag) => (
                          <span key={tag} className="rounded-full bg-bg-surface px-2 py-0.5 text-[10px] font-mono text-text-muted border border-border-subtle">{tag}</span>
                        ))}
                      </div>
                    )}
                    <div className="mt-4 pt-3 border-t border-border-subtle">
                      <p className="text-[10px] font-mono text-text-muted">
                        {detailEntry.created_at ? new Date(detailEntry.created_at).toLocaleString() : "—"}
                      </p>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl border border-dashed border-border-subtle p-8 text-center">
                    <Search className="h-8 w-8 text-text-muted/30 mx-auto mb-3" />
                    <p className="text-xs text-text-muted">Select a memory to view details</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      <MemoryEditor open={editorOpen} onOpenChange={setEditorOpen} onSaved={handleSaved} entry={editingEntry} />
      <MemoryDetail open={detailOpen} onOpenChange={setDetailOpen} entry={detailEntry} onEdit={openEditEditor} onDeleted={handleDeleted} />
    </PageTransition>
  );
}
