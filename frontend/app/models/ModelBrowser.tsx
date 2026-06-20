"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Search, Filter, Loader2 } from "lucide-react";
import ModelCard from "./ModelCard";
import Skeleton from "@/shared/ui/Skeleton";
import { modelsApi } from "@/shared/api";
import { useSystemWebSocket } from "@/shared/hooks/useSystemWebSocket";
import type { ModelInfo, HardwareInfo } from "@/shared/types";

const MODEL_TYPES = ["all", "chat", "code", "vision", "embedding", "reasoning", "lightweight"] as const;
type FilterType = (typeof MODEL_TYPES)[number];

const SIZE_FILTERS = ["all", "<3B", "3-8B", "8-14B", "14-34B", "34B+"] as const;
type SizeFilter = (typeof SIZE_FILTERS)[number];

function parseParamCount(paramCount: string): number {
  const match = paramCount.match(/([\d.]+)/);
  return match ? parseFloat(match[1]) : 0;
}

function matchesSizeFilter(paramCount: string, filter: SizeFilter): boolean {
  if (filter === "all") return true;
  const n = parseParamCount(paramCount);
  switch (filter) {
    case "<3B": return n < 3;
    case "3-8B": return n >= 3 && n <= 8;
    case "8-14B": return n > 8 && n <= 14;
    case "14-34B": return n > 14 && n <= 34;
    case "34B+": return n > 34;
    default: return true;
  }
}

interface ModelBrowserProps {
  onModelSelect?: (model: ModelInfo) => void;
}

export default function ModelBrowser({ onModelSelect }: ModelBrowserProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [sizeFilter, setSizeFilter] = useState<SizeFilter>("all");
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searching, setSearching] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const autocompleteTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [modelsRes, hardwareRes] = await Promise.all([
        modelsApi.list(),
        modelsApi.hardware(),
      ]);
      setModels(modelsRes.models);
      setHardware(hardwareRes);
    } catch {
      // Silent fail — UI will show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Close suggestions on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleAutocomplete = useCallback((value: string) => {
    setSearchQuery(value);
    if (autocompleteTimer.current) clearTimeout(autocompleteTimer.current);
    if (value.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    autocompleteTimer.current = setTimeout(async () => {
      try {
        const res = await modelsApi.autocomplete(value.trim());
        setSuggestions(res.suggestions);
        setShowSuggestions(res.suggestions.length > 0);
      } catch {
        setSuggestions([]);
      }
    }, 250);
  }, []);

  const handleSearchSubmit = useCallback(async (query?: string) => {
    const q = (query ?? searchQuery).trim();
    if (!q) return;
    setSearching(true);
    setShowSuggestions(false);
    try {
      const res = await modelsApi.search(q, {
        ...(activeFilter !== "all" ? { model_type: activeFilter } : {}),
      });
      setModels(res.models);
    } catch {
      // Fall back to client-side filter on existing list
    } finally {
      setSearching(false);
    }
  }, [searchQuery, activeFilter]);

  // Live download progress via WebSocket
  useSystemWebSocket({
    path: "/ws/models",
    enabled: downloadingModels.size > 0,
    onMessage(event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "model_progress" && Array.isArray(data.models)) {
          for (const m of data.models) {
            const progress = m.progress;
            setDownloadProgress((prev) => new Map(prev).set(m.name, progress));
            if (progress >= 1.0) {
              setDownloadingModels((prev) => {
                const next = new Set(prev);
                next.delete(m.name);
                return next;
              });
              // Refresh model list to mark as downloaded
              fetchData();
            }
          }
        }
      } catch {}
    },
  });

  const handleDownload = async (modelName: string, variant?: string) => {
    try {
      await modelsApi.download(modelName, variant);
      const downloadKey = variant ? `${modelName}:${variant}` : modelName;
      setDownloadingModels((prev) => new Set(prev).add(downloadKey));
      setDownloadProgress((prev) => new Map(prev).set(downloadKey, 0));
    } catch {
      // Error handling could show a toast
    }
  };

  const handleCancel = async (modelName: string) => {
    try {
      await modelsApi.cancel(modelName);
      setDownloadingModels((prev) => {
        const next = new Set(prev);
        next.delete(modelName);
        return next;
      });
      setDownloadProgress((prev) => {
        const next = new Map(prev);
        next.delete(modelName);
        return next;
      });
    } catch {
      // Error handling could show a toast
    }
  };

  const filteredModels = models.filter((model) => {
    const matchesSearch =
      searchQuery === "" ||
      model.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFilter =
      activeFilter === "all" || model.model_type === activeFilter;

    const matchesSize = matchesSizeFilter(model.parameter_count, sizeFilter);

    return matchesSearch && matchesFilter && matchesSize;
  });

  const modelCounts = {
    all: models.length,
    chat: models.filter((m) => m.model_type === "chat").length,
    code: models.filter((m) => m.model_type === "code").length,
    vision: models.filter((m) => m.model_type === "vision").length,
    embedding: models.filter((m) => m.model_type === "embedding").length,
    reasoning: 0,
    lightweight: 0,
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {/* Search skeleton */}
        <div className="flex gap-3">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-24" />
        </div>
        {/* Grid skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search with autocomplete */}
        <div className="relative flex-1" ref={searchRef}>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => handleAutocomplete(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleSearchSubmit();
              }
            }}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            className="w-full h-10 pl-10 pr-10 rounded-xl bg-bg-surface border border-border-subtle
                       text-sm text-text placeholder:text-text-muted
                       focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20
                       transition-colors"
          />
          {searching && (
            <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted animate-spin" />
          )}
          {showSuggestions && suggestions.length > 0 && (
            <ul className="absolute z-20 top-full mt-1 w-full rounded-xl bg-bg-surface border border-border-subtle shadow-lg max-h-48 overflow-y-auto">
              {suggestions.map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-2 text-sm text-text hover:bg-bg-hover transition-colors"
                    onMouseDown={() => {
                      setSearchQuery(s);
                      setShowSuggestions(false);
                      handleSearchSubmit(s);
                    }}
                  >
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-bg-surface border border-border-subtle">
          {MODEL_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => setActiveFilter(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeFilter === type
                  ? "bg-accent/15 text-accent"
                  : "text-text-secondary hover:text-text hover:bg-bg-hover"
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
              <span className="ml-1.5 text-text-muted">
                {modelCounts[type]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Size Filter */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-text-muted">Size:</span>
        <div className="flex items-center gap-1 p-1 rounded-xl bg-bg-surface border border-border-subtle">
          {SIZE_FILTERS.map((size) => (
            <button
              key={size}
              onClick={() => setSizeFilter(size)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-colors ${
                sizeFilter === size
                  ? "bg-accent/15 text-accent"
                  : "text-text-secondary hover:text-text hover:bg-bg-hover"
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Model Grid */}
      {filteredModels.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Filter size={40} className="text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text mb-1">No models found</h3>
          <p className="text-sm text-text-secondary">
            {searchQuery
              ? `No results for "${searchQuery}"`
              : "No models match the selected filter."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredModels.map((model) => (
            <ModelCard
              key={model.name}
              model={model}
              hardware={hardware}
              onDownload={handleDownload}
              onCancel={handleCancel}
              downloadProgress={downloadProgress.get(model.name) ?? null}
              isDownloading={Array.from(downloadingModels).some(
                (key) => key === model.name || key.startsWith(`${model.name}:`)
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
}
