"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { repository } from "../api";

interface GraphViewProps {
  repoId: number;
  onClose: () => void;
}

interface GraphNode {
  id: number;
  name?: string;
  label?: string;
  type?: string;
}

interface GraphEdge {
  id?: number;
  source: number;
  target: number;
  label?: string;
}

export function GraphView({ repoId, onClose }: GraphViewProps) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await repository.getGraph(repoId);
      setNodes(result.nodes ?? []);
      setEdges(result.edges ?? []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load graph",
      );
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const handleBuild = useCallback(async () => {
    setBuilding(true);
    setError(null);
    try {
      await repository.buildGraph(repoId);
      await fetchGraph();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to build graph",
      );
    } finally {
      setBuilding(false);
    }
  }, [repoId, fetchGraph]);

  const hasGraph = nodes.length > 0;

  return (
    <Card className="space-y-4" role="region" aria-label="Repository graph">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Graph View</h3>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleBuild}
            loading={building}
          >
            Build Graph
          </Button>
          <Button size="sm" variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded border border-danger/20 bg-danger/5 px-3 py-2 text-xs text-danger">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-8 text-center text-sm text-text-muted">
          Loading graph...
        </div>
      )}

      {/* Empty state */}
      {!loading && !hasGraph && !error && (
        <EmptyState
          title="No graph data"
          description="Build the graph to visualize repository structure."
        />
      )}

      {/* Graph data */}
      {!loading && hasGraph && (
        <>
          {/* Stats */}
          <div className="flex items-center gap-4 text-xs text-text-secondary">
            <span>
              <strong className="text-text-primary">{nodes.length}</strong>{" "}
              node{nodes.length !== 1 ? "s" : ""}
            </span>
            <span>
              <strong className="text-text-primary">{edges.length}</strong>{" "}
              edge{edges.length !== 1 ? "s" : ""}
            </span>
          </div>

          {/* Node pills */}
          <div className="flex flex-wrap gap-2">
            {nodes.map((node) => (
              <span
                key={node.id}
                className="inline-flex items-center rounded-full border border-accent/20 bg-accent/8 px-3 py-1 font-mono text-xs font-medium text-accent"
              >
                {node.name || node.label || `#${node.id}`}
              </span>
            ))}
          </div>
        </>
      )}
    </Card>
  );
}
