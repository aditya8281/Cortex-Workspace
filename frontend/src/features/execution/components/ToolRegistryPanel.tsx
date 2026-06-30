"use client";

import { useState, useCallback, useEffect } from "react";
import { tools, type ToolInfo } from "../api";

function categoryColor(category: string) {
  const map: Record<string, string> = {
    system: "bg-accent/10 text-accent",
    data: "bg-success/10 text-success",
    file: "bg-warning/10 text-warning",
    network: "bg-purple-400/10 text-purple-400",
  };
  return map[category] ?? "bg-bg-surface text-text-muted";
}

interface ToolRegistryPanelProps {
  onSelectTool?: (tool: ToolInfo) => void;
}

export function ToolRegistryPanel({ onSelectTool }: ToolRegistryPanelProps) {
  const [toolsList, setToolsList] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("");

  const loadTools = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await tools.list();
      setToolsList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tools");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTools();
  }, [loadTools]);

  const categories = Array.from(new Set(toolsList.map((t) => t.category))).sort();
  const filtered = filter
    ? toolsList.filter(
        (t) =>
          t.category === filter ||
          t.name.toLowerCase().includes(filter.toLowerCase()),
      )
    : toolsList;

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilter("")}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              !filter
                ? "bg-accent text-void"
                : "bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover"
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                filter === cat
                  ? "bg-accent text-void"
                  : "bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <button
          onClick={loadTools}
          disabled={loading}
          className="px-3 py-1.5 rounded-md text-sm font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-3"
            >
              <div className="h-4 w-32 bg-bg-surface rounded animate-pulse" />
              <div className="h-3 w-20 bg-bg-surface rounded animate-pulse" />
              <div className="h-3 w-full bg-bg-surface rounded animate-pulse" />
              <div className="h-3 w-3/4 bg-bg-surface rounded animate-pulse" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="rounded border border-danger/20 bg-danger/5 p-4 flex items-center justify-between">
          <p className="text-sm text-danger">{error}</p>
          <button
            onClick={loadTools}
            className="px-3 py-1.5 rounded-md text-sm font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && filtered.length === 0 && (
        <div className="text-center py-12 text-text-muted text-sm">
          {filter ? "No tools match this filter." : "No tools registered."}
        </div>
      )}

      {/* Tool grid */}
      {!loading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((tool) => (
            <div
              key={tool.name}
              className={`bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-2 hover:shadow-md transition-shadow ${
                onSelectTool ? "cursor-pointer hover:border-accent/40" : ""
              }`}
              onClick={() => onSelectTool?.(tool)}
            >
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-title font-medium text-text-primary font-mono text-sm">
                  {tool.name}
                </h4>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium shrink-0 ${categoryColor(tool.category)}`}
                >
                  {tool.category}
                </span>
              </div>
              <p className="text-body text-text-secondary text-xs leading-relaxed line-clamp-2">
                {tool.description}
              </p>
              <div className="flex items-center gap-3 text-xs text-text-muted">
                {Object.keys(tool.parameters).length > 0 && (
                  <span>{Object.keys(tool.parameters).length} params</span>
                )}
                {tool.requires_confirmation && (
                  <span className="text-warning">Requires confirmation</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
