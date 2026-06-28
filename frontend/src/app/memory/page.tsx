"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { StatusDot } from "@/shared/ui/StatusDot";
import { episodicMemory, semanticMemory, workingMemory, memoryGraph, memorySearch, type EpisodicMemory, type SemanticMemory, type GraphStats } from "@/features/memory/api";

type Tab = "episodic" | "semantic" | "working" | "graph" | "search";

export default function MemoryPage() {
  const [tab, setTab] = useState<Tab>("episodic");
  const [searchQuery, setSearchQuery] = useState("");
  const [episodic, setEpisodic] = useState<EpisodicMemory[]>([]);
  const [semantic, setSemantic] = useState<SemanticMemory[]>([]);
  const [working, setWorking] = useState<any[]>([]);
  const [graphStats, setGraphStats] = useState<GraphStats | null>(null);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const loader = {
      episodic: () => episodicMemory.list().then(r => setEpisodic(r.items)).catch(e => setError(e.message)),
      semantic: () => semanticMemory.list().then(r => setSemantic(r.items)).catch(e => setError(e.message)),
      working: () => workingMemory.list().then(r => setWorking(r.items)).catch(e => setError(e.message)),
      graph: () => memoryGraph.stats().then(setGraphStats).catch(e => setError(e.message)),
      search: () => Promise.resolve(),
    };
    loader[tab]().finally(() => setLoading(false));
  }, [tab]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await memorySearch.search({ query: searchQuery, limit: 20 });
      setSearchResults(res.items);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: "episodic", label: "Episodic", count: episodic.length },
    { key: "semantic", label: "Semantic", count: semantic.length },
    { key: "working", label: "Working", count: working.length },
    { key: "graph", label: "Graph", count: graphStats?.total_nodes ?? 0 },
    { key: "search", label: "Search", count: searchResults.length },
  ];

  return (
    <AppShell>
      <div className="max-w-5xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-headline font-semibold text-text-primary">Memory</h1>
          <p className="text-sm text-text-secondary mt-1">Episodic, semantic, and working memory with graph connections</p>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-border-subtle mb-6 overflow-x-auto">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors duration-150 ${
                tab === t.key
                  ? "border-b-2 border-accent text-accent"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {t.label}
              {t.count > 0 && (
                <span className="ml-1.5 text-xs text-text-muted">({t.count})</span>
              )}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {/* Episodic Tab */}
        {tab === "episodic" && (
          <div className="space-y-3">
            {episodic.length === 0 && !loading && (
              <EmptyState message="No episodic memories yet. They'll appear as conversations happen." />
            )}
            {episodic.map(m => (
              <Card key={m.id} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-text-primary leading-relaxed">{m.content}</p>
                    <div className="flex items-center gap-3 mt-2">
                      {m.emotion_tags.map(tag => (
                        <Badge key={tag} variant="default">{tag}</Badge>
                      ))}
                      <span className="text-xs text-text-muted">
                        importance: {(m.importance * 100).toFixed(0)}%
                      </span>
                      <span className="text-xs text-text-muted">
                        confidence: {(m.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-text-muted whitespace-nowrap flex-shrink-0">
                    {new Date(m.created_at).toLocaleDateString()}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Semantic Tab */}
        {tab === "semantic" && (
          <div className="space-y-3">
            {semantic.length === 0 && !loading && (
              <EmptyState message="No semantic memories yet. Facts and preferences will appear here." />
            )}
            {semantic.map(m => (
              <Card key={m.id} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-text-primary leading-relaxed">{m.content}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <Badge variant="default">{m.category}</Badge>
                      {m.source && <span className="text-xs text-text-muted">source: {m.source}</span>}
                      <span className="text-xs text-text-muted">
                        confidence: {(m.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-text-muted whitespace-nowrap flex-shrink-0">
                    {new Date(m.created_at).toLocaleDateString()}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Working Tab */}
        {tab === "working" && (
          <div className="space-y-3">
            {working.length === 0 && !loading && (
              <EmptyState message="Working memory is session-scoped. Active items appear during conversations." />
            )}
            {working.map(m => (
              <Card key={m.id} className="p-4">
                <div className="flex items-center gap-3">
                  <StatusDot
                    color={m.slot === "active" ? "success" : m.slot === "buffer" ? "accent" : "warning"}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-text-primary">{m.content}</p>
                    <span className="text-xs text-text-muted">slot: {m.slot} · priority: {m.priority}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Graph Tab */}
        {tab === "graph" && (
          <div className="space-y-4">
            {graphStats ? (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatCard label="Nodes" value={String(graphStats.total_nodes)} />
                  <StatCard label="Edges" value={String(graphStats.total_edges)} />
                  <StatCard label="Density" value={`${(graphStats.density * 100).toFixed(1)}%`} />
                  <StatCard label="Node Types" value={String(Object.keys(graphStats.node_types).length)} />
                </div>
                <Card className="p-4">
                  <h3 className="text-sm font-semibold text-text-primary mb-3">Node Types</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(graphStats.node_types).map(([type, count]) => (
                      <Badge key={type} variant="default">{type}: {count}</Badge>
                    ))}
                  </div>
                </Card>
                <Card className="p-4">
                  <h3 className="text-sm font-semibold text-text-primary mb-3">Edge Types</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(graphStats.edge_types).map(([type, count]) => (
                      <Badge key={type} variant="default">{type}: {count}</Badge>
                    ))}
                  </div>
                </Card>
              </>
            ) : (
              <EmptyState message="Graph stats loading..." />
            )}
          </div>
        )}

        {/* Search Tab */}
        {tab === "search" && (
          <div className="space-y-4">
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <Input
                  label="Search memories"
                  placeholder="Search across all memory types..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>
              <Button onClick={handleSearch} disabled={loading || !searchQuery.trim()}>
                Search
              </Button>
            </div>
            <div className="space-y-3">
              {searchResults.map((r, i) => (
                <Card key={i} className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-text-primary leading-relaxed">{r.content}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <Badge variant="default">{r.memory_type}</Badge>
                        <span className="text-xs text-text-muted">score: {(r.score * 100).toFixed(0)}%</span>
                        <span className="text-xs text-text-muted">importance: {(r.importance * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
              {searchResults.length === 0 && searchQuery && !loading && (
                <EmptyState message="No results found for this query." />
              )}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </div>
        )}
      </div>
    </AppShell>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="h-10 w-10 rounded-lg bg-bg-surface flex items-center justify-center mb-3">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted">
          <circle cx="9" cy="9" r="7" />
          <path d="M9 6v4M9 12.5v.5" />
        </svg>
      </div>
      <p className="text-sm text-text-secondary">{message}</p>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="p-4 text-center">
      <p className="text-headline font-semibold text-text-primary">{value}</p>
      <p className="text-xs text-text-muted mt-1">{label}</p>
    </Card>
  );
}
