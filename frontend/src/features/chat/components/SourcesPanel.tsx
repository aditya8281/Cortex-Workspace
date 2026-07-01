"use client";

import { useState } from "react";

interface Source {
  title: string;
  path: string;
  score: number;
  snippet: string;
}

interface SourcesPanelProps {
  sources: Source[];
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="border-t border-border-subtle mt-4 pt-3">
      <button
        onClick={() => setExpanded(expanded === null ? 0 : null)}
        className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary motion-safe:transition-colors motion-safe:duration-150 cursor-pointer"
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.2"
        >
          <path d="M2 2h8v8H2z" />
          <path d="M4 6h4M4 4h4M4 8h2" />
        </svg>
        {sources.length} source{sources.length !== 1 ? "s" : ""}
        <svg
          width="10"
          height="10"
          viewBox="0 0 10 10"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.2"
          className={`motion-safe:transition-transform duration-150 ${
            expanded !== null ? "rotate-180" : ""
          }`}
        >
          <path d="M2 3.5l3 3 3-3" />
        </svg>
      </button>
      {expanded !== null && (
        <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
          {sources.map((source, i) => (
            <div
              key={i}
              className="p-2 rounded-md bg-bg-surface border border-border-subtle"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-secondary font-mono truncate">
                  {source.path}
                </span>
                <span className="text-[10px] text-text-muted">
                  {Math.round(source.score * 100)}%
                </span>
              </div>
              <p className="text-[10px] text-text-muted line-clamp-2">
                {source.snippet}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
