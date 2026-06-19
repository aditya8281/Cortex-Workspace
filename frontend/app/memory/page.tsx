"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Brain, Search, RefreshCw, Tag, LayoutGrid, Hash, FileText, Code2, StickyNote, Lightbulb } from "lucide-react";
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
import NeuralNetwork from "../../src/shared/ui/NeuralNetwork";

type ViewMode = "list" | "search";

const categoryIcons: Record<string, typeof Brain> = {
  code: Code2,
  document: FileText,
  note: StickyNote,
  idea: Lightbulb,
};

const categoryColors: Record<string, string> = {
  code: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  document: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  note: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  idea: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  default: "bg-accent/10 text-accent border-accent/20",
};

const categorySidebarColors: Record<string, string> = {
  code: "text-blue-400",
  document: "text-purple-400",
  note: "text-amber-400",
  idea: "text-emerald-400",
};

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

  const displayEntries = viewMode === "search" 
    ? searchResults.map(r => r.entry).filter((e): e is MemoryEntry => e !== null)
    : entries;
  const hasMore = entries.length < total;

  return (
    <PageTransition>
      <NeuralNetwork intensity="low" />
      <div className="flex h-[calc(100vh-4rem)] bg-transparent">
        {/* Left Sidebar */}
        <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-border-subtle bg-bg-elevated/50">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-border-subtle">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <Brain className="h-4 w-4 text-accent" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text">Memory</h2>
                <p className="text-[10px] font-mono text-text-muted">{total} entries</p>
              </div>
            </div>
            <Button onClick={openNewEditor} className="w-full" size="sm">
              <Plus className="h-3.5 w-3.5" />
              New Memory
            </Button>
          </div>

          {/* Categories */}
          <div className="flex-1 overflow-y-auto p-3">
            <p className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-2 px-1">
              Categories
            </p>
            <nav className="space-y-0.5">
              <button
                onClick={() => setSelectedCategory(null)}
                className={cn(
                  "w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs transition-all duration-200",
                  !selectedCategory
                    ? "bg-accent-faint text-accent font-medium"
                    : "text-text-secondary hover:bg-bg-hover hover:text-text"
                )}
              >
                <LayoutGrid className="h-3.5 w-3.5 shrink-0" />
                <span className="flex-1 text-left">All Memories</span>
                <span className={cn(
                  "text-[10px] font-mono tabular-nums",
                  !selectedCategory ? "text-accent" : "text-text-muted"
                )}>
                  {total}
                </span>
              </button>
              {Object.entries(categories).map(([cat, count]) => {
                const Icon = categoryIcons[cat] || Tag;
                const isActive = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(isActive ? null : cat)}
                    className={cn(
                      "w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs transition-all duration-200",
                      isActive
                        ? "bg-accent-faint text-accent font-medium"
                        : "text-text-secondary hover:bg-bg-hover hover:text-text"
                    )}
                  >
                    <Icon className={cn("h-3.5 w-3.5 shrink-0", !isActive && (categorySidebarColors[cat] || "text-text-muted"))} />
                    <span className="flex-1 text-left capitalize">{cat}</span>
                    <span className={cn(
                      "text-[10px] font-mono tabular-nums",
                      isActive ? "text-accent" : "text-text-muted"
                    )}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </nav>

            {/* All Tags */}
            {(() => {
              const allTags = new Map<string, number>();
              entries.forEach(e => e.tags?.forEach(t => allTags.set(t, (allTags.get(t) || 0) + 1)));
              if (allTags.size === 0) return null;
              return (
                <div className="mt-6">
                  <p className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-2 px-1">
                    Tags
                  </p>
                  <div className="flex flex-wrap gap-1.5 px-1">
                    {Array.from(allTags.entries()).slice(0, 12).map(([tag, count]) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 rounded-full bg-bg-surface px-2 py-0.5 text-[10px] font-mono text-text-muted border border-border-subtle"
                      >
                        <Hash className="h-2.5 w-2.5" />
                        {tag}
                        <span className="text-text-muted/50">({count})</span>
                      </span>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Sidebar Footer */}
          <div className="p-3 border-t border-border-subtle">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-bg-surface">
              <RefreshCw className="h-3 w-3 text-text-muted" />
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">Auto-sync</span>
              <span className="ml-auto h-1.5 w-1.5 rounded-full bg-success shadow-[0_0_6px_rgba(34,197,94,0.4)]" />
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top Bar */}
          <div className="shrink-0 px-6 py-4 border-b border-border-subtle bg-bg-elevated/30">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                {/* Mobile sidebar trigger */}
                <div className="md:hidden">
                  <Button variant="ghost" size="sm" onClick={openNewEditor}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-text flex items-center gap-2">
                    <span className="hidden md:inline">
                      {selectedCategory ? (
                        <span className="capitalize">{selectedCategory}</span>
                      ) : (
                        "All Memories"
                      )}
                    </span>
                    <span className="md:hidden">Memory</span>
                  </h1>
                  <p className="text-xs text-text-muted">
                    {total} {total === 1 ? "memory" : "memories"} stored
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => fetchList(true)}>
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
                <Button onClick={openNewEditor} className="md:hidden">
                  <Plus className="h-4 w-4" />
                  New
                </Button>
              </div>
            </div>

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

          {/* Error */}
          {error && (
            <div className="mx-6 mt-4 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
              {error}
            </div>
          )}

          {/* Content Area */}
          <div className="flex-1 flex min-h-0">
            {/* Entries List */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
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
                  {viewMode !== "search" && (
                    <Button onClick={openNewEditor} className="mt-4">
                      <Plus className="h-4 w-4" />
                      Add First Memory
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <AnimatePresence mode="popLayout">
                    {displayEntries.map((entry) => {
                      const searchResult = viewMode === "search" 
                        ? searchResults.find(r => r.entry?.id === entry.id)
                        : null;
                      return (
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
                            {searchResult?.score !== undefined && (
                              <span className="text-[10px] font-mono text-text-muted">
                                {(searchResult.score * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                        </div>
                        {entry.tags && entry.tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {entry.tags.map((tag: string) => (
                              <span key={tag} className="rounded-full bg-bg-surface px-2 py-0.5 text-[10px] font-mono text-text-muted border border-border-subtle">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </motion.button>
                      );
                    })}
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

            {/* Right Detail Panel */}
            <div className="hidden lg:block w-96 shrink-0 border-l border-border-subtle bg-bg-elevated/30 overflow-y-auto">
              <div className="sticky top-0 p-5">
                <AnimatePresence mode="wait">
                  {detailEntry ? (
                    <motion.div
                      key={detailEntry.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.2 }}
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
      </div>

      <MemoryEditor open={editorOpen} onOpenChange={setEditorOpen} onSaved={handleSaved} entry={editingEntry} />
      <MemoryDetail open={detailOpen} onOpenChange={setDetailOpen} entry={detailEntry} onEdit={openEditEditor} onDeleted={handleDeleted} />
    </PageTransition>
  );
}
