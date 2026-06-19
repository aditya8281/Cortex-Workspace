"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Plus, Brain } from "lucide-react";
import { motion } from "framer-motion";
import Button from "../../src/shared/ui/Button";
import PageTransition from "../../src/shared/ui/PageTransition";
import StaggerChildren from "../../src/shared/ui/StaggerChildren";
import type { MemoryEntry, MemorySearchResult } from "../../src/shared/types";
import {
  apiListMemory,
  apiSearchMemory,
} from "../../src/shared/auth/cortexApi";
import MemorySearch from "./MemorySearch";
import MemoryEditor from "./MemoryEditor";
import MemoryDetail from "./MemoryDetail";

type ViewMode = "list" | "search";

export default function MemoryPage() {
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

  return (
    <PageTransition>
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text flex items-center gap-2">
              <Brain className="h-6 w-6 text-accent" />
              Memory
            </h1>
            <p className="mt-1 text-sm text-text-muted">
              {total} {total === 1 ? "memory" : "memories"} stored
            </p>
          </div>
          <Button onClick={openNewEditor}>
            <Plus className="h-4 w-4" />
            New Memory
          </Button>
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

        {loading && entries.length === 0 ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-xl bg-bg-elevated border border-border-subtle"
              />
            ))}
          </div>
        ) : displayEntries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Brain className="h-12 w-12 text-text-muted/40 mb-4" />
            <p className="text-sm text-text-muted">
              {viewMode === "search"
                ? "No results found"
                : "No memories yet. Create your first memory!"}
            </p>
          </div>
        ) : (
          <StaggerChildren className="space-y-2">
            {displayEntries.map((entry) => (
              <motion.button
                key={entry.id}
                onClick={() => openDetail(entry)}
                className="w-full rounded-xl border border-border-subtle bg-bg-elevated p-4 text-left transition-all duration-200 hover:border-border-accent hover:shadow-glow hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.995]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-semibold text-text truncate">
                      {entry.title}
                    </h3>
                    <p className="mt-1 text-xs text-text-muted line-clamp-2">
                      {entry.content}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider text-accent border border-accent/20">
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
                      <span
                        key={tag}
                        className="rounded-full bg-bg-surface px-2 py-0.5 text-[10px] font-mono text-text-muted border border-border-subtle"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </motion.button>
            ))}
          </StaggerChildren>
        )}

        {viewMode === "list" && hasMore && (
          <div className="mt-6 flex justify-center">
            <Button variant="secondary" loading={loading} onClick={() => fetchList()}>
              Load More
            </Button>
          </div>
        )}
      </div>

      <MemoryEditor
        open={editorOpen}
        onOpenChange={setEditorOpen}
        onSaved={handleSaved}
        entry={editingEntry}
      />

      <MemoryDetail
        open={detailOpen}
        onOpenChange={setDetailOpen}
        entry={detailEntry}
        onEdit={openEditEditor}
        onDeleted={handleDeleted}
      />
    </PageTransition>
  );
}
