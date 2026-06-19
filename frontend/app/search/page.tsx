"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Brain, Code2, RefreshCw, GitBranch } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Button from "../../src/shared/ui/Button";
import PageTransition from "../../src/shared/ui/PageTransition";
import type { SearchResult, Repository, GraphNode } from "../../src/shared/types";
import { searchApi } from "../../src/shared/api/search";
import { repoApi } from "../../src/shared/api/repo";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { cn } from "../../src/lib/utils";
import SearchFilters from "./SearchFilters";
import SearchResults from "./SearchResults";
import GraphView from "./GraphView";
import NeuralNetwork from "../../src/shared/ui/NeuralNetwork";

type Tab = "search" | "graph";

export default function SearchPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("search");
  const [selectedRepoId, setSelectedRepoId] = useState<number | undefined>(undefined);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [authLoading, user, router]);

  // Load repos on mount
  useEffect(() => {
    repoApi
      .list()
      .then((data) => setRepos(data.repos))
      .catch(() => {});
  }, []);

  const executeSearch = useCallback(
    async (searchQuery: string, filters?: { repo_id?: number; node_type?: string; language?: string; max_results?: number }) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const data = await searchApi.unified(searchQuery, filters);
        setResults(data.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  // Debounced search
  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    if (query.trim()) {
      searchTimerRef.current = setTimeout(() => executeSearch(query), 300);
    } else {
      setResults([]);
    }
    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    };
  }, [query, executeSearch]);

  function handleFilterChange(filters: { repo_id?: number; node_type?: string; language?: string; max_results: number }) {
    setSelectedRepoId(filters.repo_id);
    if (query.trim()) {
      executeSearch(query, filters);
    }
  }

  return (
    <PageTransition>
      <NeuralNetwork intensity="low" />
      <div className="flex flex-col h-[calc(100vh-4rem)] bg-transparent">
        {/* Header */}
        <div className="shrink-0 px-6 py-4 border-b border-border-subtle bg-bg-elevated/30">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-lg font-bold text-text flex items-center gap-2">
                <Search className="h-5 w-5 text-accent" />
                Unified Search
              </h1>
              <p className="text-xs text-text-muted">
                Search across code and memories
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* Tab toggle */}
              <div className="flex rounded-lg border border-border-subtle bg-bg-surface p-0.5">
                <button
                  onClick={() => setTab("search")}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all",
                    tab === "search"
                      ? "bg-accent/15 text-accent"
                      : "text-text-muted hover:text-text-secondary",
                  )}
                >
                  <Search className="h-3 w-3" />
                  Search
                </button>
                <button
                  onClick={() => setTab("graph")}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all",
                    tab === "graph"
                      ? "bg-accent/15 text-accent"
                      : "text-text-muted hover:text-text-secondary",
                  )}
                >
                  <GitBranch className="h-3 w-3" />
                  Graph
                </button>
              </div>
            </div>
          </div>

          {/* Search input */}
          <div className="relative mb-3">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search code, functions, classes, memories..."
              className="w-full rounded-xl bg-bg-surface border border-border-subtle pl-10 pr-4 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10 focus:shadow-glow"
            />
            {loading && (
              <RefreshCw className="absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted animate-spin" />
            )}
          </div>

          {/* Filters */}
          <SearchFilters repos={repos} onFilterChange={handleFilterChange} />
        </div>

        {/* Error */}
        {error && (
          <div className="mx-6 mt-4 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <AnimatePresence mode="wait">
            {tab === "search" ? (
              <motion.div
                key="search"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {!query.trim() && results.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <motion.div
                      animate={{ y: [0, -8, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    >
                      <Brain className="h-16 w-16 text-accent/30 mb-4" />
                    </motion.div>
                    <p className="text-sm font-medium text-text mb-1">Search your codebase</p>
                    <p className="text-xs text-text-muted max-w-xs">
                      Type a query to search across indexed code and memory entries.
                      Results are enriched with graph relationships.
                    </p>
                  </div>
                ) : (
                  <SearchResults results={results} onSelect={(r) => setSelectedNode(r as any)} />
                )}
              </motion.div>
            ) : (
              <motion.div
                key="graph"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {selectedRepoId ? (
                  <GraphView repoId={selectedRepoId} onSelectNode={setSelectedNode} />
                ) : (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <GitBranch className="h-16 w-16 text-accent/30 mb-4" />
                    <p className="text-sm font-medium text-text mb-1">Select a repository</p>
                    <p className="text-xs text-text-muted max-w-xs">
                      Choose a repository from the filters to view its knowledge graph.
                    </p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  );
}
