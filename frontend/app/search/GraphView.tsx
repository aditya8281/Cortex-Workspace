"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "../../src/lib/utils";
import type { GraphNode, GraphEdge, GraphData } from "../../src/shared/types";
import { searchApi } from "../../src/shared/api/search";

interface GraphViewProps {
  repoId: number;
  onSelectNode?: (node: GraphNode) => void;
}

const NODE_COLORS: Record<string, string> = {
  function: "#06b6d4",
  method: "#06b6d4",
  class: "#8b5cf6",
  file: "#64748b",
  code: "#f59e0b",
};

const EDGE_COLORS: Record<string, string> = {
  calls: "rgba(6,182,212,0.3)",
  imports: "rgba(139,92,246,0.3)",
  inherits: "rgba(245,158,11,0.3)",
  contains: "rgba(100,116,139,0.2)",
};

export default function GraphView({ repoId, onSelectNode }: GraphViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const nodePositions = useRef<Map<number, { x: number; y: number }>>(new Map());

  useEffect(() => {
    setLoading(true);
    searchApi
      .getGraph(repoId)
      .then(setGraph)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [repoId]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || !graph) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Size canvas to container
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;

    // Simple force-directed layout (grid fallback)
    const positions = new Map<number, { x: number; y: number }>();
    const cols = Math.ceil(Math.sqrt(graph.nodes.length));
    const cellW = width / (cols + 1);
    const cellH = height / (Math.ceil(graph.nodes.length / cols) + 1);

    graph.nodes.forEach((node, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      positions.set(node.id, {
        x: cellW * (col + 1),
        y: cellH * (row + 1),
      });
    });

    nodePositions.current = positions;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Draw edges
    for (const edge of graph.edges) {
      const source = positions.get(edge.source_id);
      const target = positions.get(edge.target_id);
      if (!source || !target) continue;

      ctx.strokeStyle = EDGE_COLORS[edge.edge_type] || "rgba(255,255,255,0.1)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.stroke();
    }

    // Draw nodes
    for (const node of graph.nodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;

      const color = NODE_COLORS[node.node_type] || "#64748b";
      const radius = 6;

      // Node circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.fill();

      // Glow for hovered node
      if (hoveredNode?.id === node.id) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius + 3, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Label
      ctx.fillStyle = "#e2e8f0";
      ctx.font = "10px monospace";
      ctx.fillText(node.name.slice(0, 20), pos.x + radius + 4, pos.y + 3);
    }
  }, [graph, hoveredNode]);

  // Handle mouse move for hover
  function handleMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas || !graph) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let found: GraphNode | null = null;
    for (const node of graph.nodes) {
      const pos = nodePositions.current.get(node.id);
      if (!pos) continue;
      const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (dist < 12) {
        found = node;
        break;
      }
    }
    setHoveredNode(found);
    canvas.style.cursor = found ? "pointer" : "default";
  }

  function handleClick() {
    if (hoveredNode && onSelectNode) {
      onSelectNode(hoveredNode);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[400px] rounded-xl border border-border-subtle bg-bg-elevated">
        <div className="text-sm text-text-muted">Loading graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[400px] rounded-xl border border-border-subtle bg-bg-elevated">
        <div className="text-sm text-error">{error}</div>
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] rounded-xl border border-dashed border-border-subtle bg-bg-elevated">
        <div className="text-center">
          <p className="text-sm text-text-muted">No graph data</p>
          <p className="text-xs text-text-muted/60 mt-1">Index a repository and build the graph first</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full h-[400px]">
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
        className="w-full h-full rounded-xl border border-border-subtle bg-bg-elevated"
      />
      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-2">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5 text-[10px] font-mono text-text-muted">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
            {type}
          </div>
        ))}
      </div>
      {/* Tooltip */}
      {hoveredNode && (
        <div className="absolute top-3 right-3 rounded-lg border border-border-subtle bg-bg-surface px-3 py-2 text-xs shadow-elevated">
          <p className="font-mono font-medium text-text">{hoveredNode.name}</p>
          <p className="text-text-muted mt-0.5">
            {hoveredNode.node_type} — {hoveredNode.file_path}
          </p>
        </div>
      )}
    </div>
  );
}
