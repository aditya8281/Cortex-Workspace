"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { BrainIcon, SearchIcon, DocumentIcon, CodeIcon, VaultIcon } from "@/shared/ui/icons";
import { cn } from "@/shared/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────

interface KnowledgeHealth {
  status: string;
  documents_indexed: number;
  total_chunks: number;
  graph_nodes: number;
  graph_edges: number;
  repos_indexed: number;
  code_chunks: number;
}

interface KnowledgeStats {
  documents_by_type: Record<string, number>;
  chunks_by_language: Record<string, number>;
  avg_chunks_per_document: number;
  graph_edge_types: Record<string, number>;
}

interface RetrievalMetrics {
  total_searches: number;
  avg_results: number;
  avg_latency_ms: number;
  avg_top_score: number;
  zero_result_rate: number;
}

// ── Component helpers ─────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  trend,
  color = "accent",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: { dir: "up" | "down"; label: string };
  color?: "accent" | "red" | "success" | "warning";
}) {
  const colorMap = {
    accent: "border-accent/20",
    red: "border-accent-red/20",
    success: "border-success/20",
    warning: "border-warning/20",
  };

  return (
    <div className={cn(
      "rounded-xl border p-4",
      "bg-bg-widget backdrop-blur-xl",
      colorMap[color],
      "motion-safe:transition-all motion-safe:duration-200",
    )}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-text-muted">{icon}</span>
        <p className="text-xs text-text-muted font-medium">{label}</p>
      </div>
      <p className="text-2xl font-semibold text-text-primary tabular-nums mb-1">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {trend && (
        <p className={cn(
          "text-[11px]",
          trend.dir === "up" ? "text-success" : "text-text-muted",
        )}>
          {trend.label}
        </p>
      )}
    </div>
  );
}

function MetricBar({ label, value, max, color = "accent" }: { label: string; value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-text-muted w-24 flex-shrink-0 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-bg-surface overflow-hidden">
        <div
          className={cn("h-full rounded-full motion-safe:transition-[width] duration-500 ease-out", {
            "bg-accent": color === "accent",
            "bg-accent-red": color === "red",
            "bg-success": color === "success",
            "bg-warning": color === "warning",
          })}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-text-secondary font-mono w-12 text-right tabular-nums">{value}</span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-border-subtle p-4 bg-bg-widget">
            <div className="h-3 w-16 bg-bg-surface rounded animate-pulse mb-3" />
            <div className="h-7 w-20 bg-bg-surface rounded animate-pulse mb-2" />
            <div className="h-2 w-12 bg-bg-surface rounded animate-pulse" />
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-border-subtle p-5 bg-bg-widget">
        <div className="h-4 w-24 bg-bg-surface rounded animate-pulse mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-4 w-full bg-bg-surface rounded animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────

const API_BASE = "";

export default function BrainPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [health, setHealth] = useState<KnowledgeHealth | null>(null);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [metrics, setMetrics] = useState<RetrievalMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/auth");
  }, [user, authLoading, router]);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, statsRes, metricsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/memory/knowledge/health`, { credentials: "include" }),
        fetch(`${API_BASE}/api/v1/memory/knowledge/stats`, { credentials: "include" }),
        fetch(`${API_BASE}/api/v1/memory/knowledge/retrieval-metrics`, { credentials: "include" }),
      ]);

      if (!healthRes.ok) throw new Error(`Health check failed: ${healthRes.status}`);
      setHealth(await healthRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
      if (metricsRes.ok) setMetrics(await metricsRes.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load brain data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSync = useCallback(async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/memory/scan-repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ repo_path: "." }),
      });
      if (!res.ok) throw new Error(`Sync failed: ${res.status}`);
      setSyncResult("Sync queued successfully");
      // Refresh data after a moment
      setTimeout(fetchAll, 2000);
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }, [fetchAll]);

  if (authLoading || !user) return null;

  // ── Render ───────────────────────────────────────────────────────

  const isEmpty = health && health.total_chunks === 0 && health.graph_nodes === 0;

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="flex-1 px-6 pt-6 pb-8 max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">Brain</h1>
            <p className="text-sm text-text-secondary mt-0.5">
              Memory management, indexing, and knowledge graph
            </p>
          </div>
          <button
            onClick={handleSync}
            disabled={syncing}
            aria-label={isEmpty ? "Index knowledge base" : "Re-sync knowledge base"}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium",
              "bg-accent-red text-white",
              "hover:bg-accent-red/90",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          >
            <svg
              width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"
              className={cn(syncing && "animate-spin")}
            >
              <path d="M2 8a6 6 0 0 1 11.4-3M14 8a6 6 0 0 1-11.4 3" strokeLinecap="round" />
              <path d="M13.5 2v3h-3M2.5 14v-3h3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {syncing ? "Syncing…" : (isEmpty ? "Index Now" : "Re-sync")}
          </button>
        </div>

        {/* Sync result */}
        {syncResult && (
          <div className={cn(
            "rounded-lg border px-4 py-3 mb-4 text-sm",
            syncResult.includes("failed") ? "border-danger/20 bg-danger/5 text-danger" : "border-success/20 bg-success/5 text-success",
          )}>
            {syncResult}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 mb-4">
            <p className="text-sm text-danger">{error}</p>
            <button onClick={fetchAll} className="mt-1 text-xs text-danger underline">Retry</button>
          </div>
        )}

        {loading ? (
          <LoadingSkeleton />
        ) : isEmpty ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <BrainIcon size={40} className="text-text-muted/20 mb-4" />
            <p className="text-title font-semibold text-text-primary mb-1">No indexed data yet</p>
            <p className="text-sm text-text-muted max-w-md mb-6">
              Index files, documents, and code to build your knowledge base.
              Start by scanning a repository or adding managed paths.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleSync}
                disabled={syncing}
                aria-label="Scan repository for indexing"
                className={cn(
                  "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium",
                  "bg-accent-red text-white hover:bg-accent-red/90",
                  "motion-safe:transition-colors motion-safe:duration-150",
                )}
              >
                <DocumentIcon size={16} />
                Scan Repository
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Health overview cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <StatCard
                label="Documents"
                value={health?.documents_indexed ?? 0}
                icon={<DocumentIcon size={16} />}
                color="accent"
              />
              <StatCard
                label="Chunks"
                value={health?.total_chunks ?? 0}
                icon={<BrainIcon size={16} />}
                color="success"
              />
              <StatCard
                label="Graph Nodes"
                value={health?.graph_nodes ?? 0}
                icon={<SearchIcon size={16} />}
                color="warning"
              />
              <StatCard
                label="Code Chunks"
                value={health?.code_chunks ?? 0}
                icon={<CodeIcon size={16} />}
                color="red"
              />
            </div>

            {/* Detailed stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Documents by type */}
              {stats && Object.keys(stats.documents_by_type).length > 0 && (
                <div className="rounded-xl border border-border-subtle p-4 bg-bg-widget backdrop-blur-xl">
                  <h3 className="text-sm font-semibold text-text-primary mb-3">Documents by Type</h3>
                  <div className="space-y-2">
                    {Object.entries(stats.documents_by_type)
                      .sort(([, a], [, b]) => b - a)
                      .map(([type, count]) => {
                        const maxCount = Math.max(...Object.values(stats.documents_by_type));
                        return <MetricBar key={type} label={type} value={count} max={maxCount} />;
                      })}
                  </div>
                </div>
              )}

              {/* Chunks by language */}
              {stats && Object.keys(stats.chunks_by_language).length > 0 && (
                <div className="rounded-xl border border-border-subtle p-4 bg-bg-widget backdrop-blur-xl">
                  <h3 className="text-sm font-semibold text-text-primary mb-3">Chunks by Language</h3>
                  <div className="space-y-2">
                    {Object.entries(stats.chunks_by_language)
                      .sort(([, a], [, b]) => b - a)
                      .map(([lang, count]) => {
                        const maxCount = Math.max(...Object.values(stats.chunks_by_language));
                        return <MetricBar key={lang} label={lang} value={count} max={maxCount} />;
                      })}
                  </div>
                </div>
              )}
            </div>

            {/* Retrieval metrics */}
            {metrics && metrics.total_searches > 0 && (
              <div className="rounded-xl border border-border-subtle p-4 bg-bg-widget backdrop-blur-xl mb-6">
                <h3 className="text-sm font-semibold text-text-primary mb-3">Retrieval Performance</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <p className="text-xs text-text-muted">Total Searches</p>
                    <p className="text-lg font-semibold text-text-primary tabular-nums">{metrics.total_searches}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Avg Results</p>
                    <p className="text-lg font-semibold text-text-primary tabular-nums">{metrics.avg_results.toFixed(1)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Avg Latency</p>
                    <p className="text-lg font-semibold text-text-primary tabular-nums">{metrics.avg_latency_ms.toFixed(0)}ms</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Avg Top Score</p>
                    <p className="text-lg font-semibold text-text-primary tabular-nums">{metrics.avg_top_score.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Zero Result Rate</p>
                    <p className="text-lg font-semibold text-text-primary tabular-nums">{(metrics.zero_result_rate * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            )}

            {/* Knowledge graph placeholder */}
            <div className="rounded-xl border border-border-subtle p-5 bg-bg-widget backdrop-blur-xl">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text-primary">Knowledge Graph</h3>
                <span className="text-[10px] px-2 py-0.5 rounded bg-accent/12 text-accent font-medium">v1.09</span>
              </div>
              <div className="flex flex-col items-center justify-center py-8 text-center rounded-lg bg-bg-surface">
                <SearchIcon size={28} className="text-text-muted/20 mb-3" />
                <p className="text-sm text-text-muted mb-1">
                  Interactive graph visualization coming in v1.09
                </p>
                <p className="text-xs text-text-muted/60">
                  {health?.graph_nodes ?? 0} nodes and {health?.graph_edges ?? 0} edges indexed
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
