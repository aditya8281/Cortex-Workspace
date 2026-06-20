"use client";

import { useCallback, useEffect, useRef, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Plus, Brain, Search, RefreshCw, Hash, LayoutGrid, Network, List, ChevronDown, ChevronRight, FolderSync, Loader2, Check, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Button from "../../src/shared/ui/Button";
import PageTransition from "../../src/shared/ui/PageTransition";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import type { MemoryEntry, MemorySearchResult } from "../../src/shared/types";
import {
  apiListMemory,
  apiSearchMemory,
} from "../../src/shared/auth/cortexApi";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { cn } from "../../src/lib/utils";
import { api } from "@/shared/api/client";
import MemorySearch from "./MemorySearch";
import MemoryEditor from "./MemoryEditor";
import MemoryDetail from "./MemoryDetail";

type ViewMode = "list" | "search";
type DisplayView = "graph" | "list";

interface WatchedPath {
  path: string;
  repo_id: number | null;
  embedding_model: string;
  sync_enabled: boolean;
  initial_scan_job_id: string | null;
  initial_scan_status: string | null;
}

interface SyncStatusData {
  watching: number;
  pending_changes: number;
  indexed_files: number;
  errors: number;
  status: string;
  last_sync: string | null;
  watched_paths: WatchedPath[];
}

interface SyncJobData {
  job_id: string;
  repo_path: string;
  job_type: string;
  status: string;
  progress: number;
  total: number | null;
  result: { files_scanned?: number; chunks_created?: number } | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

import { syncApi } from "@/shared/api/sync";
import type { SyncDefaultPath, EmbeddingModelOption } from "@/shared/api/sync";

const categoryColors: Record<string, string> = {
  code: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  document: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  note: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  idea: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  default: "bg-accent/10 text-accent border-accent/20",
};

const categoryNodeColors: Record<string, string> = {
  code: "#3b82f6",
  document: "#a855f7",
  note: "#f59e0b",
  idea: "#10b981",
};

const categoryChipColors: Record<string, string> = {
  code: "bg-blue-500/10 text-blue-400 border-blue-500/30 hover:bg-blue-500/20",
  document: "bg-purple-500/10 text-purple-400 border-purple-500/30 hover:bg-purple-500/20",
  note: "bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20",
  idea: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20",
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

  const [displayView, setDisplayView] = useState<DisplayView>("graph");
  const [detailPanelOpen, setDetailPanelOpen] = useState(true);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<MemoryEntry | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailEntry, setDetailEntry] = useState<MemoryEntry | null>(null);

  const [offset, setOffset] = useState(0);
  const limit = 20;

  const [syncStatus, setSyncStatus] = useState<SyncStatusData | null>(null);
  const [syncJobs, setSyncJobs] = useState<SyncJobData[]>([]);
  const [showSyncPrompt, setShowSyncPrompt] = useState(false);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [syncRepoPath, setSyncRepoPath] = useState("");
  const [syncRepoPathValid, setSyncRepoPathValid] = useState<boolean | null>(null);
  const [syncRepoPathChecking, setSyncRepoPathChecking] = useState(false);
  const [syncRepoPathResolved, setSyncRepoPathResolved] = useState("");
  const [syncEmbeddingModel, setSyncEmbeddingModel] = useState("nomic-embed-text");
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncError, setSyncError] = useState("");
  const [syncDefaults, setSyncDefaults] = useState<{
    defaultPaths: SyncDefaultPath[];
    excludeDirs: string[];
    embeddingModels: EmbeddingModelOption[];
  } | null>(null);
  const [syncSelectedPaths, setSyncSelectedPaths] = useState<Record<string, boolean>>({});
  const [syncExcludeDirs, setSyncExcludeDirs] = useState<string[]>([]);
  const [syncNewExcludeDir, setSyncNewExcludeDir] = useState("");
  const [syncShowExcludeList, setSyncShowExcludeList] = useState(false);

  const fetchSyncStatus = useCallback(async () => {
    try {
      const data = await api.get<SyncStatusData>("/api/v1/sync/status");
      setSyncStatus(data);
      if (data.watched_paths.length === 0) {
        setShowSyncPrompt(true);
      }
    } catch {}
  }, []);

  const fetchSyncJobs = useCallback(async () => {
    try {
      const data = await api.get<SyncJobData[]>("/api/v1/sync/jobs");
      setSyncJobs(data);
    } catch {}
  }, []);

  useEffect(() => {
    fetchSyncStatus();
    fetchSyncJobs();
    const interval = setInterval(() => {
      fetchSyncStatus();
      fetchSyncJobs();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchSyncStatus, fetchSyncJobs]);

  useEffect(() => {
    if (!syncModalOpen) return;
    syncApi.defaults().then((data) => {
      setSyncDefaults({
        defaultPaths: data.default_paths,
        excludeDirs: data.exclude_dirs,
        embeddingModels: data.embedding_models,
      });
      const initial: Record<string, boolean> = {};
      data.default_paths.forEach((p) => { initial[p.path] = p.enabled; });
      setSyncSelectedPaths(initial);
      setSyncExcludeDirs(data.exclude_dirs);
      setSyncEmbeddingModel(data.embedding_models[0]?.value ?? "nomic-embed-text");
    }).catch(() => {});
  }, [syncModalOpen]);

  // Debounced custom path validation
  useEffect(() => {
    if (!syncRepoPath.trim()) {
      setSyncRepoPathValid(null);
      setSyncRepoPathChecking(false);
      setSyncRepoPathResolved("");
      return;
    }
    setSyncRepoPathChecking(true);
    const timer = setTimeout(async () => {
      try {
        const result = await syncApi.validatePath(syncRepoPath.trim());
        setSyncRepoPathValid(result.exists);
        setSyncRepoPathResolved(result.resolved_path);
      } catch {
        setSyncRepoPathValid(false);
      } finally {
        setSyncRepoPathChecking(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [syncRepoPath]);

  const handleStartSync = async (e: React.FormEvent) => {
    e.preventDefault();
    const pathsToSync = Object.entries(syncSelectedPaths)
      .filter(([, enabled]) => enabled)
      .map(([path]) => path);
    if (syncRepoPath.trim()) pathsToSync.push(syncRepoPath.trim());
    if (pathsToSync.length === 0) {
      setSyncError("Select at least one directory or enter a custom path");
      return;
    }
    setSyncLoading(true);
    setSyncError("");
    try {
      for (const path of pathsToSync) {
        await syncApi.start(path, syncEmbeddingModel, syncExcludeDirs);
      }
      setSyncRepoPath("");
      setSyncModalOpen(false);
      setShowSyncPrompt(false);
      await fetchSyncStatus();
      await fetchSyncJobs();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Failed to start sync");
    } finally {
      setSyncLoading(false);
    }
  };

  const handleStopSync = async (repoPath: string) => {
    try {
      await api.post("/api/v1/sync/stop", { repo_path: repoPath });
      await fetchSyncStatus();
    } catch (err) {
      console.error("Failed to stop sync:", err);
    }
  };

  const activeJob = syncJobs.find(
    (j) => j.status === "pending" || j.status === "running"
  );

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
    setDetailPanelOpen(true);
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

  const categoryList = useMemo(() => Object.keys(categories), [categories]);

  const graphNodes = useMemo(() => {
    const nodes: { id: string; label: string; x: number; y: number; color: string; count: number; type: "category" }[] = [];
    const catEntries = categoryList;
    const cx = 400;
    const cy = 250;
    const radius = 160;
    catEntries.forEach((cat, i) => {
      const angle = (2 * Math.PI * i) / catEntries.length - Math.PI / 2;
      nodes.push({
        id: `cat-${cat}`,
        label: cat,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        color: categoryNodeColors[cat] || "#06b6d4",
        count: categories[cat] || 0,
        type: "category",
      });
    });
    return nodes;
  }, [categoryList, categories]);

  const graphEdges = useMemo(() => {
    const edges: { from: string; to: string; color: string }[] = [];
    displayEntries.forEach((entry) => {
      const catNode = graphNodes.find(n => n.id === `cat-${entry.category}`);
      if (catNode) {
        edges.push({
          from: catNode.id,
          to: String(entry.id),
          color: catNode.color,
        });
      }
    });
    return edges;
  }, [displayEntries, graphNodes]);

  const graphEntryNodes = useMemo(() => {
    const entryNodes: { id: string; label: string; x: number; y: number; color: string; entry: MemoryEntry }[] = [];
    const catPositions: Record<string, { x: number; y: number }> = {};
    graphNodes.forEach(n => { catPositions[n.id] = { x: n.x, y: n.y }; });

    const grouped: Record<string, MemoryEntry[]> = {};
    displayEntries.forEach(e => {
      const catKey = `cat-${e.category}`;
      if (!grouped[catKey]) grouped[catKey] = [];
      grouped[catKey].push(e);
    });

    Object.entries(grouped).forEach(([catKey, catEntries]) => {
      const catPos = catPositions[catKey];
      if (!catPos) return;
      const catColor = categoryNodeColors[catKey.replace("cat-", "")] || "#06b6d4";
      catEntries.forEach((entry, i) => {
        const angle = (2 * Math.PI * i) / catEntries.length + Math.PI / 6;
        const dist = 100 + (i % 3) * 20;
        entryNodes.push({
          id: String(entry.id),
          label: entry.title.length > 20 ? entry.title.slice(0, 20) + "…" : entry.title,
          x: catPos.x + dist * Math.cos(angle),
          y: catPos.y + dist * Math.sin(angle),
          color: catColor,
          entry,
        });
      });
    });
    return entryNodes;
  }, [displayEntries, graphNodes]);

  return (
    <DashboardShell>
      <PageTransition>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="shrink-0 border-b border-border-subtle">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-accent/10 flex items-center justify-center">
                  <Brain className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-text">
                    {selectedCategory ? (
                      <span className="capitalize">{selectedCategory}</span>
                    ) : (
                      "Memory"
                    )}
                  </h1>
                  <p className="text-xs text-text-muted">
                    {total} {total === 1 ? "entry" : "entries"} · Knowledge Graph
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center rounded-lg border border-border-subtle bg-bg-surface p-0.5">
                  <button
                    onClick={() => setDisplayView("graph")}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                      displayView === "graph"
                        ? "bg-accent/10 text-accent"
                        : "text-text-muted hover:text-text-secondary"
                    )}
                  >
                    <Network className="h-3.5 w-3.5" />
                    Graph
                  </button>
                  <button
                    onClick={() => setDisplayView("list")}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                      displayView === "list"
                        ? "bg-accent/10 text-accent"
                        : "text-text-muted hover:text-text-secondary"
                    )}
                  >
                    <List className="h-3.5 w-3.5" />
                    List
                  </button>
                </div>
                <Button variant="ghost" size="sm" onClick={() => fetchList(true)}>
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
                <Button onClick={openNewEditor} size="sm">
                  <Plus className="h-3.5 w-3.5" />
                  New Memory
                </Button>
                <button
                  onClick={() => setDetailPanelOpen(!detailPanelOpen)}
                  className="hidden lg:flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-colors"
                >
                  {detailPanelOpen ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  Detail
                </button>
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

            {/* Category Filter Chips */}
            <div className="flex items-center gap-2 mt-3 overflow-x-auto pb-1">
              <button
                onClick={() => setSelectedCategory(null)}
                className={cn(
                  "shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all",
                  !selectedCategory
                    ? "bg-accent/10 text-accent border-accent/30"
                    : "bg-bg-surface text-text-muted border-border-subtle hover:border-border-accent hover:text-text-secondary"
                )}
              >
                <LayoutGrid className="h-3 w-3" />
                All
                <span className="font-mono text-[10px]">{total}</span>
              </button>
              {categoryList.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                  className={cn(
                    "shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all capitalize",
                    selectedCategory === cat
                      ? (categoryChipColors[cat] || "bg-accent/10 text-accent border-accent/30")
                      : "bg-bg-surface text-text-muted border-border-subtle hover:border-border-accent hover:text-text-secondary"
                  )}
                >
                  {cat}
                  <span className="font-mono text-[10px] opacity-60">{categories[cat] || 0}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Auto-Sync Prompt */}
          {showSyncPrompt && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-3 rounded-xl border border-accent/20 bg-accent/5 p-4"
            >
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-xl bg-accent/10 flex items-center justify-center shrink-0">
                  <FolderSync className="h-5 w-5 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-text mb-1">Enable Auto-Sync</h3>
                  <p className="text-xs text-text-muted mb-3">
                    Automatically sync your code files to memory. Choose a directory to watch and select an embedding model.
                  </p>
                  <div className="flex items-center gap-2">
                    <Button size="sm" onClick={() => setSyncModalOpen(true)}>
                      <FolderSync className="h-3.5 w-3.5" />
                      Start Auto-Sync
                    </Button>
                    <button
                      onClick={() => setShowSyncPrompt(false)}
                      className="text-xs text-text-muted hover:text-text-secondary transition-colors px-2 py-1"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Active Sync Progress */}
          {activeJob && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-3 rounded-xl border border-accent/20 bg-accent/5 p-3"
            >
              <div className="flex items-center gap-3">
                <Loader2 className="h-4 w-4 animate-spin text-accent shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-text">
                    {activeJob.status === "pending" ? "Initial scan queued..." : "Indexing files..."}
                  </p>
                  <p className="text-[10px] text-text-muted truncate">
                    {activeJob.repo_path}
                  </p>
                </div>
                {activeJob.progress > 0 && activeJob.total && (
                  <div className="text-xs font-mono text-text-muted">
                    {activeJob.progress}/{activeJob.total}
                  </div>
                )}
              </div>
              {activeJob.total && (
                <div className="mt-2 h-1 bg-bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-300"
                    style={{ width: `${activeJob.total ? (activeJob.progress / activeJob.total) * 100 : 0}%` }}
                  />
                </div>
              )}
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <div className="mx-0 mt-3 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
              {error}
            </div>
          )}

          {/* Content Area */}
          <div className="flex-1 flex min-h-0 mt-3">
            <div className="flex-1 overflow-y-auto min-w-0">
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
              ) : displayView === "graph" ? (
                /* ── Graph View ── */
                <div className="w-full h-full min-h-[500px] rounded-xl border border-border-subtle bg-bg-elevated/50 overflow-hidden">
                  <svg
                    viewBox="0 0 800 500"
                    className="w-full h-full"
                    preserveAspectRatio="xMidYMid meet"
                  >
                    <defs>
                      <filter id="glow">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feMerge>
                          <feMergeNode in="blur" />
                          <feMergeNode in="SourceGraphic" />
                        </feMerge>
                      </filter>
                      {categoryList.map((cat) => (
                        <radialGradient key={cat} id={`grad-${cat}`}>
                          <stop offset="0%" stopColor={categoryNodeColors[cat] || "#06b6d4"} stopOpacity="0.3" />
                          <stop offset="100%" stopColor={categoryNodeColors[cat] || "#06b6d4"} stopOpacity="0" />
                        </radialGradient>
                      ))}
                    </defs>

                    {/* Edges */}
                    {graphEdges.map((edge, i) => {
                      const entryNode = graphEntryNodes.find(n => n.id === edge.to);
                      const catNode = graphNodes.find(n => n.id === edge.from);
                      if (!entryNode || !catNode) return null;
                      return (
                        <line
                          key={`edge-${i}`}
                          x1={catNode.x}
                          y1={catNode.y}
                          x2={entryNode.x}
                          y2={entryNode.y}
                          stroke={edge.color}
                          strokeOpacity="0.15"
                          strokeWidth="1"
                        />
                      );
                    })}

                    {/* Category glow halos */}
                    {graphNodes.map((node) => (
                      <circle
                        key={`halo-${node.id}`}
                        cx={node.x}
                        cy={node.y}
                        r={50}
                        fill={`url(#grad-${node.label})`}
                      />
                    ))}

                    {/* Category nodes */}
                    {graphNodes.map((node) => (
                      <g
                        key={node.id}
                        className="cursor-pointer"
                        onClick={() => setSelectedCategory(selectedCategory === node.label ? null : node.label)}
                      >
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={28}
                          fill="#0a0a0f"
                          stroke={node.color}
                          strokeWidth={selectedCategory === node.label ? 2.5 : 1.5}
                          filter="url(#glow)"
                          opacity={selectedCategory && selectedCategory !== node.label ? 0.4 : 1}
                        />
                        <text
                          x={node.x}
                          y={node.y - 2}
                          textAnchor="middle"
                          dominantBaseline="middle"
                          fill={node.color}
                          fontSize="11"
                          fontWeight="600"
                          fontFamily="Inter, sans-serif"
                          className="capitalize"
                        >
                          {node.label}
                        </text>
                        <text
                          x={node.x}
                          y={node.y + 12}
                          textAnchor="middle"
                          dominantBaseline="middle"
                          fill="#555566"
                          fontSize="9"
                          fontFamily="JetBrains Mono, monospace"
                        >
                          {node.count}
                        </text>
                      </g>
                    ))}

                    {/* Entry nodes */}
                    {graphEntryNodes.map((node) => (
                      <g
                        key={node.id}
                        className="cursor-pointer"
                        onClick={() => openDetail(node.entry)}
                      >
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={5}
                          fill={node.color}
                          opacity={selectedCategory && selectedCategory !== node.entry.category ? 0.2 : 0.7}
                          className="transition-opacity hover:opacity-100"
                        />
                        <title>{node.entry.title}</title>
                      </g>
                    ))}

                    {graphNodes.length === 0 && (
                      <text x="400" y="250" textAnchor="middle" fill="#555566" fontSize="13" fontFamily="Inter, sans-serif">
                        No categories to display
                      </text>
                    )}
                  </svg>
                </div>
              ) : (
                /* ── List View ── */
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
                                  <Hash className="h-2.5 w-2.5 inline -mr-0.5" />
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

              {viewMode === "list" && displayView === "list" && hasMore && (
                <div className="mt-6 flex justify-center">
                  <Button variant="secondary" loading={loading} onClick={() => fetchList()}>
                    Load More
                  </Button>
                </div>
              )}
            </div>

            {/* Right Detail Panel */}
            <AnimatePresence>
              {detailPanelOpen && (
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 384, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="hidden lg:block shrink-0 border-l border-border-subtle bg-bg-elevated/30 overflow-hidden"
                >
                  <div className="w-96 p-5">
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
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <MemoryEditor open={editorOpen} onOpenChange={setEditorOpen} onSaved={handleSaved} entry={editingEntry} />
        <MemoryDetail open={detailOpen} onOpenChange={setDetailOpen} entry={detailEntry} onEdit={openEditEditor} onDeleted={handleDeleted} />

        {/* Sync Modal */}
        {syncModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-bg-elevated rounded-xl border border-border-subtle shadow-2xl w-full max-w-lg mx-4 max-h-[85vh] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-border-subtle shrink-0">
                <div className="flex items-center gap-2">
                  <FolderSync size={16} className="text-accent" />
                  <h2 className="text-sm font-semibold text-text">Auto-Sync Setup</h2>
                </div>
                <button
                  onClick={() => setSyncModalOpen(false)}
                  className="text-text-muted hover:text-text transition-colors"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleStartSync} className="p-4 space-y-4 overflow-y-auto flex-1 min-h-0">
                {/* Default Home Directories */}
                {syncDefaults?.defaultPaths && syncDefaults.defaultPaths.length > 0 && (
                  <div>
                    <label className="block text-xs font-medium text-text-muted mb-2">
                      Home Directories (auto-synced by default)
                    </label>
                    <div className="space-y-1.5">
                      {syncDefaults.defaultPaths.map((dp) => (
                        <label
                          key={dp.path}
                          className={cn(
                            "flex items-center gap-3 p-2.5 rounded-lg border transition-all cursor-pointer",
                            syncSelectedPaths[dp.path]
                              ? "border-accent/30 bg-accent/5"
                              : "border-border-subtle bg-bg-surface hover:border-border-default",
                            !dp.exists && "opacity-50"
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={syncSelectedPaths[dp.path] ?? false}
                            onChange={(e) =>
                              setSyncSelectedPaths((prev) => ({
                                ...prev,
                                [dp.path]: e.target.checked,
                              }))
                            }
                            className="rounded border-border-subtle bg-bg-surface text-accent focus:ring-accent/20"
                            disabled={!dp.exists}
                          />
                          <div className="flex-1 min-w-0">
                            <span className="text-xs font-medium text-text">{dp.label}</span>
                            <span className="text-[10px] text-text-muted ml-2 font-mono">{dp.path}</span>
                          </div>
                          {!dp.exists && (
                            <span className="text-[10px] text-text-muted italic">not found</span>
                          )}
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* Custom Path */}
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1.5">
                    Custom Directory
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={syncRepoPath}
                      onChange={(e) => setSyncRepoPath(e.target.value)}
                      placeholder="/path/to/your/project"
                      className={cn(
                        "w-full px-3 py-2 rounded-lg bg-bg-surface border text-sm text-text placeholder:text-text-muted focus:outline-none transition-colors pr-8",
                        syncRepoPath.trim() && syncRepoPathValid === true
                          ? "border-success/50 focus:border-success"
                          : syncRepoPath.trim() && syncRepoPathValid === false
                          ? "border-error/50 focus:border-error"
                          : "border-border-subtle focus:border-accent"
                      )}
                    />
                    {/* Validation indicator */}
                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                      {syncRepoPathChecking ? (
                        <Loader2 size={14} className="animate-spin text-text-muted" />
                      ) : syncRepoPath.trim() && syncRepoPathValid === true ? (
                        <Check size={14} className="text-success" />
                      ) : syncRepoPath.trim() && syncRepoPathValid === false ? (
                        <X size={14} className="text-error" />
                      ) : null}
                    </div>
                  </div>
                  {/* Resolved path hint */}
                  {syncRepoPath.trim() && !syncRepoPathChecking && (
                    <p className={cn(
                      "mt-1 text-[10px] font-mono",
                      syncRepoPathValid === true ? "text-success/70" : "text-error/70"
                    )}>
                      {syncRepoPathResolved || "..."}
                      {syncRepoPathValid === true ? " — exists" : syncRepoPathValid === false ? " — directory not found" : ""}
                    </p>
                  )}
                </div>

                {/* Embedding Model with Technique Descriptions */}
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1.5">
                    Embedding Model
                  </label>
                  <div className="relative">
                    <select
                      value={syncEmbeddingModel}
                      onChange={(e) => setSyncEmbeddingModel(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle text-sm text-text appearance-none focus:outline-none focus:border-accent"
                    >
                      {syncDefaults?.embeddingModels.map((m) => (
                        <option key={m.value} value={m.value}>
                          {m.label} ({m.technique}, {m.dimensions}d)
                        </option>
                      ))}
                    </select>
                    <ChevronDown
                      size={14}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none"
                    />
                  </div>
                  {/* Model description */}
                  {syncDefaults?.embeddingModels.find((m) => m.value === syncEmbeddingModel) && (
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className={cn(
                        "text-[10px] font-mono",
                        syncDefaults.embeddingModels.find((m) => m.value === syncEmbeddingModel)!.speed === "fast"
                          ? "text-accent"
                          : syncDefaults.embeddingModels.find((m) => m.value === syncEmbeddingModel)!.speed === "medium"
                          ? "text-warning"
                          : syncDefaults.embeddingModels.find((m) => m.value === syncEmbeddingModel)!.speed === "slow"
                          ? "text-text-muted"
                          : "text-success"
                      )}>
                        {syncDefaults.embeddingModels.find((m) => m.value === syncEmbeddingModel)!.speed}
                      </span>
                      <span className="text-[10px] text-text-muted">
                        {syncDefaults.embeddingModels.find((m) => m.value === syncEmbeddingModel)!.description}
                      </span>
                    </div>
                  )}
                </div>

                {/* Exclude Directories */}
                <div>
                  <button
                    type="button"
                    onClick={() => setSyncShowExcludeList(!syncShowExcludeList)}
                    className="flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors"
                  >
                    Exclude Directories ({syncExcludeDirs.length})
                    <ChevronDown
                      size={12}
                      className={cn(
                        "transition-transform",
                        syncShowExcludeList && "rotate-180"
                      )}
                    />
                  </button>
                  {syncShowExcludeList && (
                    <div className="mt-2 space-y-2">
                      <div className="flex flex-wrap gap-1.5">
                        {syncExcludeDirs.map((dir) => (
                          <span
                            key={dir}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-bg-surface border border-border-subtle text-[10px] font-mono text-text-muted"
                          >
                            {dir}
                            <button
                              type="button"
                              onClick={() => setSyncExcludeDirs((prev) => prev.filter((d) => d !== dir))}
                              className="text-text-muted hover:text-error transition-colors"
                            >
                              ✕
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={syncNewExcludeDir}
                          onChange={(e) => setSyncNewExcludeDir(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              const dir = syncNewExcludeDir.trim();
                              if (dir && !syncExcludeDirs.includes(dir)) {
                                setSyncExcludeDirs((prev) => [...prev, dir]);
                                setSyncNewExcludeDir("");
                              }
                            }
                          }}
                          placeholder="Add directory to exclude"
                          className="flex-1 px-3 py-1.5 rounded-lg bg-bg-surface border border-border-subtle text-xs text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {syncError && (
                  <p className="text-xs text-error">{syncError}</p>
                )}

                <button
                  type="submit"
                  disabled={syncLoading}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                    "bg-accent text-white hover:bg-accent/90",
                    "focus:outline-none focus:ring-2 focus:ring-accent/50",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  {syncLoading && <Loader2 size={14} className="animate-spin" />}
                  Start Auto-Sync
                </button>
              </form>
            </div>
          </div>
        )}
      </PageTransition>
    </DashboardShell>
  );
}
