"use client";

import { useMemo } from "react";
import type { MemoryEntry } from "../../../src/shared/types";
const categoryNodeColors: Record<string, string> = {
  code: "#3b82f6",
  document: "#a855f7",
  note: "#f59e0b",
  idea: "#10b981",
};

interface MemoryGraphViewProps {
  entries: MemoryEntry[];
  categories: Record<string, number>;
  selectedCategory: string | null;
  onSelectCategory: (cat: string | null) => void;
  onSelectEntry: (entry: MemoryEntry) => void;
}

export default function MemoryGraphView({
  entries,
  categories,
  selectedCategory,
  onSelectCategory,
  onSelectEntry,
}: MemoryGraphViewProps) {
  const categoryList = useMemo(() => Object.keys(categories), [categories]);

  const graphNodes = useMemo(() => {
    const nodes: { id: string; label: string; x: number; y: number; color: string; count: number }[] = [];
    const cx = 400;
    const cy = 250;
    const radius = 160;
    categoryList.forEach((cat, i) => {
      const angle = (2 * Math.PI * i) / categoryList.length - Math.PI / 2;
      nodes.push({
        id: `cat-${cat}`,
        label: cat,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        color: categoryNodeColors[cat] || "#06b6d4",
        count: categories[cat] || 0,
      });
    });
    return nodes;
  }, [categoryList, categories]);

  const graphEdges = useMemo(() => {
    const edges: { from: string; to: string; color: string }[] = [];
    entries.forEach((entry) => {
      const catNode = graphNodes.find((n) => n.id === `cat-${entry.category}`);
      if (catNode) {
        edges.push({ from: catNode.id, to: String(entry.id), color: catNode.color });
      }
    });
    return edges;
  }, [entries, graphNodes]);

  const graphEntryNodes = useMemo(() => {
    const entryNodes: { id: string; label: string; x: number; y: number; color: string; entry: MemoryEntry }[] = [];
    const catPositions: Record<string, { x: number; y: number }> = {};
    graphNodes.forEach((n) => { catPositions[n.id] = { x: n.x, y: n.y }; });

    const grouped: Record<string, MemoryEntry[]> = {};
    entries.forEach((e) => {
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
  }, [entries, graphNodes]);

  return (
    <div className="w-full h-full min-h-[500px] rounded-xl border border-border-subtle bg-bg-elevated/50 overflow-hidden">
      <svg viewBox="0 0 800 500" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
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

        {graphEdges.map((edge, i) => {
          const entryNode = graphEntryNodes.find((n) => n.id === edge.to);
          const catNode = graphNodes.find((n) => n.id === edge.from);
          if (!entryNode || !catNode) return null;
          return (
            <line key={`edge-${i}`} x1={catNode.x} y1={catNode.y} x2={entryNode.x} y2={entryNode.y}
              stroke={edge.color} strokeOpacity="0.15" strokeWidth="1" />
          );
        })}

        {graphNodes.map((node) => (
          <circle key={`halo-${node.id}`} cx={node.x} cy={node.y} r={50} fill={`url(#grad-${node.label})`} />
        ))}

        {graphNodes.map((node) => (
          <g key={node.id} className="cursor-pointer" onClick={() => onSelectCategory(selectedCategory === node.label ? null : node.label)}>
            <circle cx={node.x} cy={node.y} r={28} fill="#0a0a0f" stroke={node.color}
              strokeWidth={selectedCategory === node.label ? 2.5 : 1.5} filter="url(#glow)"
              opacity={selectedCategory && selectedCategory !== node.label ? 0.4 : 1} />
            <text x={node.x} y={node.y - 2} textAnchor="middle" dominantBaseline="middle"
              fill={node.color} fontSize="11" fontWeight="600" fontFamily="Inter, sans-serif" className="capitalize">
              {node.label}
            </text>
            <text x={node.x} y={node.y + 12} textAnchor="middle" dominantBaseline="middle"
              fill="#555566" fontSize="9" fontFamily="JetBrains Mono, monospace">
              {node.count}
            </text>
          </g>
        ))}

        {graphEntryNodes.map((node) => (
          <g key={node.id} className="cursor-pointer" onClick={() => onSelectEntry(node.entry)}>
            <circle cx={node.x} cy={node.y} r={5} fill={node.color}
              opacity={selectedCategory && selectedCategory !== node.entry.category ? 0.2 : 0.7}
              className="transition-opacity hover:opacity-100" />
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
  );
}
