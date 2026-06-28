"use client";

import { useState, useEffect, useCallback } from "react";
import type { ModelWithFit, RecommendedModel, HardwareInfo, RamFitStatus } from "../api";
import { catalog, calculateRamFit, getDefaultModel } from "../api";
import { formatParamCount } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";
import { ModelCard } from "./ModelCard";

interface BrowseViewProps {
  hardware: HardwareInfo | null;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelectedIds: string[];
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
  downloadingModels: Map<string, number>;
  onCancelDownload: (modelId: string) => void;
}

type SizeFilter = "small" | "medium" | "large" | null;

export function BrowseView({
  hardware,
  onDownload,
  onViewDetail,
  compareSelectedIds,
  onToggleCompare,
  compareDisabled,
  downloadingModels,
  onCancelDownload,
}: BrowseViewProps) {
  const [models, setModels] = useState<ModelWithFit[]>([]);
  const [recommended, setRecommended] = useState<RecommendedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [capabilityFilter, setCapabilityFilter] = useState<string[]>([]);
  const [sizeFilter, setSizeFilter] = useState<SizeFilter>(null);
  const [sort, setSort] = useState<string>("relevance");
  const [totalCount, setTotalCount] = useState(0);
  const defaultModel = getDefaultModel();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let result;
      if (debouncedQuery) {
        const caps = capabilityFilter.length > 0 ? capabilityFilter.join(",") : undefined;
        result = await catalog.search({ q: debouncedQuery, capabilities: caps, limit: 200 });
        result = { ...result, models: result.models.map(m => enrichModel(m)) };
      } else {
        const res = await catalog.list({ downloaded_only: false });
        let enriched = res.models.map(m => enrichModel(m));

        // Client-side capability filter
        if (capabilityFilter.length > 0) {
          enriched = enriched.filter(m =>
            capabilityFilter.some(c => m.capabilities.includes(c))
          );
        }

        result = { models: enriched, total_count: res.total_count };
      }

      // Client-side size filter
      let filtered = result.models;
      if (sizeFilter) {
        filtered = filtered.filter(m => {
          const params = m.parameter_count ?? 0;
          if (sizeFilter === "small") return params < 4_000_000_000;
          if (sizeFilter === "medium") return params >= 4_000_000_000 && params <= 14_000_000_000;
          return params > 14_000_000_000;
        });
      }

      // Sort
      if (sort !== "relevance") {
        filtered.sort((a, b) => {
          if (sort === "size_asc") return (a.size_bytes ?? 0) - (b.size_bytes ?? 0);
          if (sort === "size_desc") return (b.size_bytes ?? 0) - (a.size_bytes ?? 0);
          if (sort === "params_asc") return (a.parameter_count ?? 0) - (b.parameter_count ?? 0);
          if (sort === "params_desc") return (b.parameter_count ?? 0) - (a.parameter_count ?? 0);
          return 0;
        });
      }

      setModels(filtered);
      setTotalCount(result.total_count);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, capabilityFilter, sizeFilter, sort, hardware]);

  const enrichModel = (m: any): ModelWithFit => {
    const ram = hardware?.ram_gb ?? 32;
    const minRam = m.hardware_requirements?.min_ram_gb ?? null;
    const { percent, status } = calculateRamFit(ram, minRam);
    return {
      ...m,
      ramFitPercent: percent,
      ramFitStatus: status,
      isDefault: m.name === defaultModel,
    };
  };

  useEffect(() => { loadModels(); }, [loadModels]);

  // Load recommended on mount
  useEffect(() => {
    catalog.recommended().then(res => {
      const all = Object.values(res.workloads).flatMap(w => w.recommendations ?? []);
      setRecommended(all.slice(0, 4));
    }).catch(() => {});
  }, []);

  const toggleCapability = (cap: string) => {
    setCapabilityFilter(prev =>
      prev.includes(cap) ? prev.filter(c => c !== cap) : [...prev, cap]
    );
  };

  const capabilities = ["chat", "code", "vision"];

  return (
    <div className="space-y-6">
      {/* Recommended */}
      {recommended.length > 0 && !debouncedQuery && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Recommended for your hardware
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {recommended.map(rec => (
              <Card key={rec.model_id} className="p-3">
                <p className="text-sm font-medium text-text-primary mb-1">
                  {rec.display_name}
                </p>
                <p className="text-xs text-text-muted mb-2 line-clamp-2">
                  {rec.explanation?.why ?? rec.description}
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="default">{formatParamCount(rec.parameter_count)}</Badge>
                  <span className="text-[0.625rem] text-text-muted">
                    score: {Math.round(rec.score * 100)}%
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <Input
            label="Search models"
            placeholder="Search by name, capability..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Capability chips */}
        <div className="flex items-center gap-1.5">
          {capabilities.map(cap => (
            <button
              key={cap}
              onClick={() => toggleCapability(cap)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-150 ${
                capabilityFilter.includes(cap)
                  ? "bg-accent/12 text-accent"
                  : "bg-bg-surface text-text-muted hover:text-text-secondary"
              }`}
            >
              {cap}
            </button>
          ))}
        </div>

        {/* Size filter */}
        <div className="flex items-center gap-1.5">
          {(["small", "medium", "large"] as const).map(size => (
            <button
              key={size}
              onClick={() => setSizeFilter(sizeFilter === size ? null : size)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-150 ${
                sizeFilter === size
                  ? "bg-accent/12 text-accent"
                  : "bg-bg-surface text-text-muted hover:text-text-secondary"
              }`}
            >
              {size === "small" ? "<4B" : size === "medium" ? "4-14B" : ">14B"}
            </button>
          ))}
        </div>

        {/* Sort */}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="h-9 rounded-md border border-border-default bg-bg-surface px-2.5 text-xs text-text-secondary focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none"
          aria-label="Sort models"
        >
          <option value="relevance">Relevance</option>
          <option value="size_asc">Size ↑</option>
          <option value="size_desc">Size ↓</option>
          <option value="params_asc">Params ↑</option>
          <option value="params_desc">Params ↓</option>
        </select>
      </div>

      {/* Results count */}
      <p className="text-xs text-text-muted">
        {totalCount > 0 ? `${totalCount} models` : ""}
      </p>

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
          {error}
          <Button size="sm" variant="ghost" className="ml-2" onClick={loadModels}>
            Retry
          </Button>
        </div>
      )}

      {/* Card grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4">
              <div className="space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
                <Skeleton className="h-1.5 w-full rounded-full" />
              </div>
            </Card>
          ))}
        </div>
      ) : models.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {models.map(model => (
            <ModelCard
              key={model.model_id}
              model={model}
              onDownload={onDownload}
              onViewDetail={onViewDetail}
              compareSelected={compareSelectedIds.includes(model.model_id)}
              onToggleCompare={onToggleCompare}
              compareDisabled={compareDisabled}
              downloading={downloadingModels.has(model.model_id)}
              downloadProgress={downloadingModels.get(model.model_id)}
              onCancelDownload={onCancelDownload}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No models found"
          description={searchQuery ? "Try a different search query or filters" : "No models available in catalog"}
        />
      )}
    </div>
  );
}
