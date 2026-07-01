"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { SearchIcon, ChatIcon, BrainIcon, CodeIcon, VaultIcon, DocumentIcon } from "@/shared/ui/icons";
import { cn } from "@/shared/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────

interface SearchResult {
  content: string;
  source: string;
  score: number;
  file_path: string;
  document_id: number | null;
  language: string | null;
  chunk_type: string | null;
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  next_cursor: string | null;
  has_more: boolean;
}

type PrefixKey = "default" | "web" | "chat" | "code" | "files" | "vault";

interface PrefixConfig {
  key: PrefixKey;
  label: string;
  icon: React.ReactNode;
  available: boolean;
  availableIn: string;
  tooltip: string;
  endpoint?: string;
}

// ── Prefix configuration ──────────────────────────────────────────────

const PREFIXES: PrefixConfig[] = [
  { key: "default", label: "All", icon: <SearchIcon size={14} />, available: true, availableIn: "", tooltip: "Search all indexed content", endpoint: "/api/v1/memory/search" },
  { key: "web", label: "/web", icon: <SearchIcon size={14} />, available: false, availableIn: "v1.11", tooltip: "Web search — planned for v1.11" },
  { key: "chat", label: "/chat", icon: <ChatIcon size={14} />, available: true, availableIn: "", tooltip: "Search conversations", endpoint: "/api/v1/memory/search" },
  { key: "code", label: "/code", icon: <CodeIcon size={14} />, available: false, availableIn: "v1.12", tooltip: "Code search — planned for v1.12" },
  { key: "files", label: "/files", icon: <DocumentIcon size={14} />, available: true, availableIn: "", tooltip: "Search indexed files", endpoint: "/api/v1/memory/search" },
  { key: "vault", label: "/vault", icon: <VaultIcon size={14} />, available: true, availableIn: "", tooltip: "Search vault contents", endpoint: "/api/v1/privacy/vault/search" },
];

// ── Quick filters ─────────────────────────────────────────────────────

const QUICK_FILTERS = [
  { key: "all", label: "All" },
  { key: "vector", label: "Vector" },
  { key: "fulltext", label: "Fulltext" },
  { key: "graph", label: "Graph" },
];

// ── Components ────────────────────────────────────────────────────────

function ResultCard({ result }: { result: SearchResult }) {
  const highlightQuery = (text: string) => {
    // Simple highlight — truncate to first 300 chars, show file context
    const maxLen = 300;
    const display = text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
    return display;
  };

  const scoreColor = result.score >= 0.7 ? "text-success" : result.score >= 0.4 ? "text-warning" : "text-text-muted";

  return (
    <div className={cn(
      "group rounded-xl border border-border-subtle p-4",
      "bg-bg-widget backdrop-blur-xl",
      "hover:border-border-default",
      "motion-safe:transition-all motion-safe:duration-200",
    )}>
      <div className="flex items-start gap-3">
        {/* Score indicator */}
        <div className={cn("flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-mono font-bold", scoreColor, "bg-bg-surface")}>
          {Math.round(result.score * 100)}
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1.5">
            {result.file_path && (
              <span className="text-xs text-text-muted font-mono truncate">
                {result.file_path}
              </span>
            )}
            {result.language && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-bg-surface text-text-muted font-mono">
                {result.language}
              </span>
            )}
            {result.chunk_type && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-bg-surface text-text-muted">
                {result.chunk_type}
              </span>
            )}
          </div>

          {/* Content snippet */}
          <p className="text-sm text-text-secondary leading-relaxed line-clamp-3">
            {highlightQuery(result.content)}
          </p>

          {/* Footer */}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[10px] text-text-muted">{result.source}</span>
            <span className="text-[10px] text-text-muted">·</span>
            <span className={cn("text-[10px] font-medium", scoreColor)}>
              {Math.round(result.score * 100)}% match
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex-shrink-0 flex gap-1 opacity-0 group-hover:opacity-100 motion-safe:transition-opacity motion-safe:duration-150">
          <button
            className="h-7 w-7 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover flex items-center justify-center motion-safe:transition-colors motion-safe:duration-150"
            aria-label="Copy result"
            title="Copy"
            onClick={() => navigator.clipboard.writeText(result.content)}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="2" width="10" height="10" rx="1" />
              <path d="M6 14h7a1 1 0 0 0 1-1V6" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border-subtle p-4 bg-bg-widget">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-bg-surface animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-48 bg-bg-surface rounded animate-pulse" />
              <div className="h-3 w-full bg-bg-surface rounded animate-pulse" />
              <div className="h-3 w-3/4 bg-bg-surface rounded animate-pulse" />
              <div className="h-2 w-24 bg-bg-surface rounded animate-pulse" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ query, prefix }: { query: string; prefix: PrefixConfig }) {
  const Icon = prefix.icon;
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <span className="text-text-muted/30 mb-4">{Icon}</span>
      <p className="text-title font-semibold text-text-primary mb-1">
        {query ? "No results found" : "Search something to begin"}
      </p>
      <p className="text-sm text-text-muted max-w-md">
        {query
          ? `No ${prefix.label.toLowerCase()} results for "${query}". Try a different prefix or search term.`
          : `Type a query and press Enter to search ${prefix.label.toLowerCase()} content.`}
      </p>
      {prefix.available && query && (
        <button
          onClick={() => {/* switch to default prefix */}}
          className="mt-4 text-xs font-medium text-accent hover:text-accent/80 transition-colors duration-150"
        >
          Search all sources instead
        </button>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SearchPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activePrefix, setActivePrefix] = useState<PrefixKey>("default");
  const [activeFilter, setActiveFilter] = useState("all");
  const [hasSearched, setHasSearched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/auth");
  }, [user, authLoading, router]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const currentPrefix = PREFIXES.find(p => p.key === activePrefix) ?? PREFIXES[0];

  const doSearch = useCallback(async (q: string, prefix: PrefixKey) => {
    const trimmed = q.trim();
    if (!trimmed) {
      setResults([]);
      setTotal(0);
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/memory/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          query: trimmed,
          max_results: 20,
          sources: activeFilter === "all" ? ["vector", "fulltext", "graph"] : [activeFilter],
          diversity: 0.3,
        }),
      });

      if (!res.ok) throw new Error(`Search failed: ${res.status}`);

      const data: SearchResponse = await res.json();
      setResults(data.results ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  // Debounced search
  const handleQueryChange = useCallback((value: string) => {
    setQuery(value);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      doSearch(value, activePrefix);
    }, 300);
  }, [activePrefix, doSearch]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
      doSearch(query, activePrefix);
    }
  }, [query, activePrefix, doSearch]);

  const handlePrefixChange = useCallback((prefix: PrefixKey) => {
    setActivePrefix(prefix);
    if (query.trim()) {
      doSearch(query, prefix);
    }
  }, [query, doSearch]);

  const handleFilterChange = useCallback((filter: string) => {
    setActiveFilter(filter);
    if (query.trim()) {
      // Re-search with new filter
      setTimeout(() => doSearch(query, activePrefix), 0);
    }
  }, [query, activePrefix, doSearch]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
  }, []);

  if (authLoading || !user) return null;

  // ── Derived ──────────────────────────────────────────────────────

  const selectedPrefix = PREFIXES.find(p => p.key === activePrefix) ?? PREFIXES[0];

  return (
    <div className="flex h-full flex-col">
      {/* Search header */}
      <div className="flex-shrink-0 px-6 pt-6 pb-4 border-b border-border-subtle">
        {/* Search bar */}
        <div className={cn(
          "mx-auto max-w-2xl flex items-center gap-3",
          "rounded-xl border border-border-subtle px-4 py-3",
          "bg-bg-widget backdrop-blur-xl",
          "focus-within:border-border-default",
          "motion-safe:transition-colors motion-safe:duration-200",
        )}>
          <SearchIcon size={18} className="text-text-muted flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search your knowledge base, files, conversations…"
            className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
          />
          {query && (
            <button
              onClick={() => { setQuery(""); setResults([]); setHasSearched(false); }}
              className="text-text-muted hover:text-text-secondary transition-colors duration-150"
              aria-label="Clear search"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <path d="M4 4l8 8m0-8l-8 8" />
              </svg>
            </button>
          )}
        </div>

        {/* Prefix chips */}
        <div className="flex items-center gap-1.5 mt-3 mx-auto max-w-2xl flex-wrap">
          {PREFIXES.map((p) => {
            const isActive = activePrefix === p.key;
            return (
              <button
                key={p.key}
                onClick={() => p.available && handlePrefixChange(p.key)}
                disabled={!p.available}
                title={p.tooltip}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium",
                  "motion-safe:transition-all motion-safe:duration-150",
                  isActive
                    ? "bg-accent-red text-white shadow-sm"
                    : p.available
                    ? "text-text-muted hover:text-text-secondary hover:bg-bg-hover"
                    : "text-text-muted/40 cursor-not-allowed",
                )}
              >
                {p.icon}
                <span>{p.label}</span>
                {!p.available && (
                  <span className="text-[9px] opacity-60 ml-0.5">({p.availableIn})</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Results */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="rounded-xl border border-danger/20 bg-danger/5 p-4 mb-4">
              <p className="text-sm text-danger">{error}</p>
              <button
                onClick={() => doSearch(query, activePrefix)}
                className="mt-2 text-xs font-medium text-danger underline hover:text-danger/80"
              >
                Retry
              </button>
            </div>
          )}

          {loading ? (
            <LoadingSkeleton />
          ) : hasSearched && results.length === 0 ? (
            <EmptyState query={query} prefix={selectedPrefix} />
          ) : (
            <>
              {hasSearched && (
                <p className="text-xs text-text-muted mb-3">
                  {total} result{total !== 1 ? "s" : ""} for &ldquo;{query}&rdquo;
                  {activePrefix !== "default" && ` in ${selectedPrefix.label}`}
                </p>
              )}
              <div className="space-y-2">
                {results.map((r, i) => (
                  <ResultCard key={`${r.document_id ?? r.file_path}-${i}`} result={r} />
                ))}
              </div>
            </>
          )}

          {/* Initial empty state */}
          {!hasSearched && !loading && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <SearchIcon size={40} className="text-text-muted/20 mb-4" />
              <p className="text-title font-semibold text-text-primary mb-1">Search CORTEX</p>
              <p className="text-sm text-text-muted max-w-md">
                Search across indexed files, conversations, code, and knowledge.
                Use prefix chips to narrow results.
              </p>
            </div>
          )}
        </div>

        {/* Filter sidebar */}
        <div className="flex-shrink-0 w-56 border-l border-border-subtle p-4 hidden md:block overflow-y-auto">
          <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider mb-3">Filters</h3>

          {/* Source filters */}
          <div className="mb-5">
            <p className="text-xs text-text-muted mb-2">Source Type</p>
            <div className="space-y-1">
              {QUICK_FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => handleFilterChange(f.key)}
                  className={cn(
                    "w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors duration-150",
                    activeFilter === f.key
                      ? "bg-accent/12 text-accent"
                      : "text-text-muted hover:text-text-secondary hover:bg-bg-hover",
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Stats */}
          {hasSearched && (
            <div className="border-t border-border-subtle pt-4">
              <p className="text-xs text-text-muted mb-2">Results</p>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Total</span>
                  <span className="text-text-secondary font-mono">{total}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Displayed</span>
                  <span className="text-text-secondary font-mono">{results.length}</span>
                </div>
                {results.length > 0 && (
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">Best score</span>
                    <span className="text-text-secondary font-mono">{Math.round(results[0].score * 100)}%</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-border-subtle my-4" />

          {/* Tips */}
          <div>
            <p className="text-xs text-text-muted mb-2">Tips</p>
            <ul className="space-y-1.5 text-[11px] text-text-muted leading-relaxed">
              <li>Use prefix chips to narrow scope</li>
              <li>Press Enter for instant search</li>
              <li>Search auto-triggers while typing</li>
              <li>Click result score for relevance</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
