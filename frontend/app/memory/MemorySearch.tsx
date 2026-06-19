"use client";

import { Search, Sparkles } from "lucide-react";
import { cn } from "../../src/lib/utils";

interface MemorySearchProps {
  query: string;
  onQueryChange: (value: string) => void;
  semantic: boolean;
  onSemanticChange: (value: boolean) => void;
  categories: Record<string, number>;
  selectedCategory: string | null;
  onCategoryChange: (category: string | null) => void;
}

export default function MemorySearch({
  query,
  onQueryChange,
  semantic,
  onSemanticChange,
  categories,
  selectedCategory,
  onCategoryChange,
}: MemorySearchProps) {
  const categoryEntries = Object.entries(categories);

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search memories..."
          className="w-full rounded-xl bg-bg-surface border border-border-subtle pl-10 pr-4 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10 focus:shadow-glow"
        />
        <button
          type="button"
          onClick={() => onSemanticChange(!semantic)}
          className={cn(
            "absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all duration-200",
            semantic
              ? "bg-accent/15 text-accent border border-accent/20"
              : "bg-bg-elevated text-text-muted border border-border-subtle hover:text-text-secondary",
          )}
        >
          <Sparkles className="h-3 w-3" />
          Semantic
        </button>
      </div>

      {categoryEntries.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => onCategoryChange(null)}
            className={cn(
              "rounded-full px-3 py-1 text-[11px] font-mono font-medium uppercase tracking-wider border transition-all duration-200",
              selectedCategory === null
                ? "bg-accent/15 text-accent border-accent/20"
                : "bg-bg-surface text-text-muted border-border-subtle hover:text-text-secondary hover:border-border-default",
            )}
          >
            All
          </button>
          {categoryEntries.map(([cat, count]) => (
            <button
              key={cat}
              type="button"
              onClick={() => onCategoryChange(selectedCategory === cat ? null : cat)}
              className={cn(
                "rounded-full px-3 py-1 text-[11px] font-mono font-medium uppercase tracking-wider border transition-all duration-200",
                selectedCategory === cat
                  ? "bg-accent/15 text-accent border-accent/20"
                  : "bg-bg-surface text-text-muted border-border-subtle hover:text-text-secondary hover:border-border-default",
              )}
            >
              {cat} ({count})
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
