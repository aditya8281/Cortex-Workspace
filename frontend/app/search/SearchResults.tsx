"use client";

import { Code2, FileText, StickyNote, Lightbulb } from "lucide-react";
import { cn } from "../../src/lib/utils";
import type { SearchResult } from "../../src/shared/types";

const typeStyles: Record<string, string> = {
  code: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  memory: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
};

const typeIcons: Record<string, typeof Code2> = {
  code: Code2,
  memory: StickyNote,
};

interface SearchResultsProps {
  results: SearchResult[];
  onSelect?: (result: SearchResult) => void;
}

export default function SearchResults({ results, onSelect }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Code2 className="h-12 w-12 text-text-muted/30 mb-3" />
        <p className="text-sm text-text-muted">No results found</p>
        <p className="text-xs text-text-muted/60 mt-1">Try a different query or adjust filters</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {results.map((result, i) => {
        const Icon = typeIcons[result.type] || FileText;
        return (
          <button
            key={`${result.type}-${result.chunk_id || result.entry?.id || i}`}
            onClick={() => onSelect?.(result)}
            className={cn(
              "w-full rounded-xl border p-4 text-left transition-all duration-200",
              "hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.995]",
              "border-border-subtle bg-bg-elevated hover:border-border-accent hover:shadow-glow",
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                {/* Header */}
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider border",
                      typeStyles[result.type] || "bg-bg-surface text-text-muted border-border-subtle",
                    )}
                  >
                    <Icon className="h-2.5 w-2.5" />
                    {result.type}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">
                    {(result.score * 100).toFixed(0)}% match
                  </span>
                  {result.language && (
                    <span className="text-[10px] font-mono text-text-muted/60">
                      {result.language}
                    </span>
                  )}
                </div>

                {/* Name */}
                <h3 className="text-sm font-semibold text-text truncate font-mono">
                  {result.name}
                </h3>

                {/* File path */}
                {result.file_path && (
                  <p className="text-xs text-text-muted mt-0.5 truncate">
                    {result.file_path}
                    {result.start_line && (
                      <span className="text-text-muted/60">:{result.start_line}</span>
                    )}
                  </p>
                )}

                {/* Content preview */}
                {result.content_preview && (
                  <p className="mt-2 text-xs text-text-secondary line-clamp-2 leading-relaxed">
                    {result.content_preview}
                  </p>
                )}

                {/* Graph context */}
                {result.context && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {result.context.calls && result.context.calls.length > 0 && (
                      <span className="text-[10px] font-mono text-text-muted">
                        calls: {result.context.calls.slice(0, 3).join(", ")}
                        {result.context.calls.length > 3 && ` +${result.context.calls.length - 3}`}
                      </span>
                    )}
                    {result.context.imports && result.context.imports.length > 0 && (
                      <span className="text-[10px] font-mono text-text-muted">
                        imports: {result.context.imports.slice(0, 3).join(", ")}
                      </span>
                    )}
                    {result.context.inherits && result.context.inherits.length > 0 && (
                      <span className="text-[10px] font-mono text-text-muted">
                        extends: {result.context.inherits.join(", ")}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Score indicator */}
              <div className="shrink-0 flex flex-col items-end gap-1">
                <div
                  className={cn(
                    "h-8 w-8 rounded-lg flex items-center justify-center text-[10px] font-mono font-bold",
                    result.score > 0.8
                      ? "bg-success/10 text-success"
                      : result.score > 0.5
                        ? "bg-accent/10 text-accent"
                        : "bg-bg-surface text-text-muted",
                  )}
                >
                  {(result.score * 100).toFixed(0)}
                </div>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
