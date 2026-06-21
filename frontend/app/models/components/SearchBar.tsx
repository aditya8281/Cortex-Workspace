"use client";

import { Search, GitCompare } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

const MODEL_TYPES = ["all", "chat", "code", "vision", "embedding", "reasoning", "fast"] as const;
const SIZE_FILTERS = ["all", "<3B", "3-8B", "8-14B", "14B+"] as const;

interface SearchBarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearchSubmit: () => void;
  activeTypeFilter: string;
  onTypeFilterChange: (type: string) => void;
  activeSizeFilter: string;
  onSizeFilterChange: (size: string) => void;
  typeCounts: Record<string, number>;
  sizeCounts: Record<string, number>;
  suggestions: string[];
  onSuggestionSelect: (suggestion: string) => void;
  onCompare: () => void;
  compareCount: number;
}

export default function SearchBar({
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  activeTypeFilter,
  onTypeFilterChange,
  activeSizeFilter,
  onSizeFilterChange,
  typeCounts,
  sizeCounts,
  suggestions,
  onSuggestionSelect,
  onCompare,
  compareCount,
}: SearchBarProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredSuggestions = suggestions.filter((s) =>
    s.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex items-center gap-3 w-full">
      {/* Search Input with Autocomplete */}
      <div ref={containerRef} className="relative flex-1">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            ref={inputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => {
              onSearchChange(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setShowSuggestions(false);
                onSearchSubmit();
              }
            }}
            placeholder="Search models..."
            className={cn(
              "w-full h-10 pl-10 pr-4 rounded-xl",
              "bg-bg-surface border border-border-subtle",
              "text-sm text-text placeholder:text-text-muted",
              "focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20",
              "transition-colors duration-200"
            )}
          />
        </div>

        {/* Autocomplete Dropdown */}
        {showSuggestions && searchQuery.length > 0 && filteredSuggestions.length > 0 && (
          <div
            className={cn(
              "absolute z-50 top-full mt-1 w-full",
              "bg-bg-elevated border border-border-subtle rounded-xl",
              "shadow-lg overflow-hidden"
            )}
          >
            {filteredSuggestions.slice(0, 6).map((suggestion) => (
              <button
                key={suggestion}
                onMouseDown={(e) => {
                  e.preventDefault();
                  onSuggestionSelect(suggestion);
                  setShowSuggestions(false);
                }}
                className={cn(
                  "w-full px-4 py-2.5 text-left text-sm text-text-secondary",
                  "hover:bg-bg-hover hover:text-text",
                  "transition-colors duration-150"
                )}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Type Filter Pills */}
      <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-bg-surface border border-border-subtle">
        {MODEL_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => onTypeFilterChange(type)}
            className={cn(
              "px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-all duration-200",
              activeTypeFilter === type
                ? "bg-accent/15 text-accent"
                : "text-text-muted hover:text-text-secondary hover:bg-bg-hover"
            )}
          >
            {type}
            {typeCounts[type] != null && (
              <span className="ml-1 opacity-60">{typeCounts[type]}</span>
            )}
          </button>
        ))}
      </div>

      {/* Size Filter Pills */}
      <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-bg-surface border border-border-subtle">
        {SIZE_FILTERS.map((size) => (
          <button
            key={size}
            onClick={() => onSizeFilterChange(size)}
            className={cn(
              "px-2 py-1 rounded-lg text-xs font-medium transition-all duration-200",
              activeSizeFilter === size
                ? "bg-accent/15 text-accent"
                : "text-text-muted hover:text-text-secondary hover:bg-bg-hover"
            )}
          >
            {size}
            {sizeCounts[size] != null && (
              <span className="ml-1 opacity-60">{sizeCounts[size]}</span>
            )}
          </button>
        ))}
      </div>

      {/* Compare Button */}
      <button
        onClick={onCompare}
        disabled={compareCount === 0}
        className={cn(
          "flex items-center gap-2 h-10 px-4 rounded-xl",
          "text-sm font-medium transition-all duration-200",
          compareCount > 0
            ? "bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20"
            : "bg-bg-surface text-text-muted border border-border-subtle opacity-50 cursor-not-allowed"
        )}
      >
        <GitCompare className="h-4 w-4" />
        Compare
        {compareCount > 0 && (
          <span className="flex items-center justify-center h-5 w-5 rounded-full bg-accent text-void text-[10px] font-bold">
            {compareCount}
          </span>
        )}
      </button>
    </div>
  );
}
