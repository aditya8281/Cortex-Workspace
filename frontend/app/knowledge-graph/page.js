"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Loader } from "../../src/shared/ui";

function GraphNode({ node, index, total }) {
  const radius = 180;
  const angle = (index / Math.max(total, 1)) * Math.PI * 2 - Math.PI / 2;
  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius;

  return (
    <div
      className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
      style={{ left: `calc(50% + ${x}px)`, top: `calc(50% + ${y}px)` }}
    >
      <div className="h-2.5 w-2.5 rounded-full bg-cortex-cyan shadow-cortex-cyan" />
      <div className="mt-cortex-8 max-w-[140px] rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-8 py-cortex-4 text-center font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
        {node}
      </div>
    </div>
  );
}

export default function KnowledgeGraphPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadGraph() {
    try {
      const response = await fetch("/api/workspace/intelligence", { cache: "no-store" });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || data?.detail || "Workspace intelligence request failed");
      }

      setReport(data);
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Workspace intelligence request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadGraph();
  }, []);

  const graph = report?.knowledge_graph || { nodes: [], edges: [] };
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const keyFiles = report?.key_files || [];
  const activityFeed = report?.activity_feed || [];

  const visibleEdges = useMemo(() => edges.slice(0, 18), [edges]);

  return (
    <section className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.4fr)_360px]">
      <div className="grid gap-cortex-16">
        <div className="flex items-start justify-between gap-cortex-16">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Knowledge Graph</p>
            <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Workspace Intelligence Graph</h1>
            <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
              Structural map of the Cortex workspace, repositories, concepts, and relationships.
            </p>
          </div>
          <div className="flex items-center gap-cortex-12">
            <Badge variant="neutral">{nodes.length} nodes</Badge>
            <Button variant="secondary" size="sm" onClick={loadGraph}>
              {loading ? (
                <span className="inline-flex items-center gap-cortex-8">
                  <Loader className="h-3.5 w-3.5" />
                  Syncing
                </span>
              ) : (
                "Refresh"
              )}
            </Button>
          </div>
        </div>

        {error ? (
          <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
            <div className="font-mono text-sm">Error: {error}</div>
          </Card>
        ) : null}

        <Card className="grid gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Graph view</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Concept network</h2>
            </div>
            <Badge variant="cyan">{edges.length} edges</Badge>
          </div>

          <div className="relative min-h-[640px] overflow-hidden rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70">
            <div className="absolute inset-0 opacity-60">
              {visibleEdges.map((edge, index) => (
                <div
                  key={`${edge.source}-${edge.target}-${index}`}
                  className="absolute left-1/2 top-1/2 h-px bg-cortex-border"
                  style={{
                    width: "320px",
                    transform: `translate(-50%, -50%) rotate(${(index / Math.max(visibleEdges.length, 1)) * 360}deg)`,
                  }}
                />
              ))}
            </div>
            {nodes.slice(0, 12).map((node, index) => (
              <GraphNode key={`${node}-${index}`} node={node} index={index} total={Math.min(nodes.length, 12)} />
            ))}
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cortex-cyan/30 bg-cortex-surface px-cortex-16 py-cortex-8 font-mono text-[11px] uppercase tracking-[0.18em] text-cortex-cyan shadow-cortex-cyan">
              cortex
            </div>
          </div>
        </Card>
      </div>

      <div className="grid gap-cortex-16">
        <Card className="grid gap-cortex-12">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Activity feed</p>
            <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Intelligence summary</h2>
          </div>
          <div className="grid gap-cortex-8">
            {activityFeed.length > 0 ? (
              activityFeed.slice(0, 6).map((item, index) => (
                <div
                  key={`${item.title}-${index}`}
                  className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12"
                >
                  <div className="flex items-center justify-between gap-cortex-12">
                    <div className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                      {item.title}
                    </div>
                    <Badge variant={item.tone === "warning" ? "warning" : item.tone === "green" ? "green" : "cyan"}>
                      {item.tone || "info"}
                    </Badge>
                  </div>
                  <div className="mt-cortex-8 text-sm text-cortex-text-muted">{item.detail}</div>
                </div>
              ))
            ) : (
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                No activity feed available.
              </div>
            )}
          </div>
        </Card>

        <Card className="grid gap-cortex-12">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Key files</p>
            <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Workspace anchors</h2>
          </div>
          <div className="grid gap-cortex-8">
            {keyFiles.length > 0 ? (
              keyFiles.slice(0, 8).map((file) => (
                <div
                  key={file}
                  className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-12 py-cortex-8 font-mono text-sm text-cortex-text-muted"
                >
                  {file}
                </div>
              ))
            ) : (
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                No key files detected.
              </div>
            )}
          </div>
        </Card>
      </div>
    </section>
  );
}
