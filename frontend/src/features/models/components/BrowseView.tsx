"use client";

import { useState, useEffect, useCallback } from "react";
import type { FamilySummary, HardwareInfo, ModelFamiliesResponse } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { calculateRamFit, getDefaultModel } from "@/features/models/api";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";
import { FamilyCard } from "./FamilyCard";
import { EmbeddingSection } from "./EmbeddingSection";

interface BrowseViewProps {
  hardware: HardwareInfo | null;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelectedIds: string[];
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
}

type SizeFilter = "small" | "medium" | "large" | null;

export function BrowseView({
  hardware,
  onDownload,
  onViewDetail,
  compareSelectedIds,
  onToggleCompare,
  compareDisabled,
}: BrowseViewProps) {
  const [data, setData] = useState<ModelFamiliesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [capabilityFilter, setCapabilityFilter] = useState<string[]>([]);
  const [sizeFilter, setSizeFilter] = useState<SizeFilter>(null);
  const [sort, setSort] = useState<string>("relevance");
  const ram_gb = hardware?.ram_gb ?? 32;

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadFamilies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await catalog.families();
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadFamilies(); }, [loadFamilies]);

  if (!data && loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
        {error}
        <Button size="sm" variant="ghost" className="ml-2" onClick={loadFamilies}>
          Retry
        </Button>
      </div>
    );
  }

  if (!data) return null;

  // Filter families
  let filteredFamilies = data.families.filter((fam) => {
    if (debouncedQuery) {
      const q = debouncedQuery.toLowerCase();
      if (
        !fam.family.toLowerCase().includes(q) &&
        !fam.display_name.toLowerCase().includes(q) &&
        !fam.default_variant.model_id.toLowerCase().includes(q)
      ) {
        return false;
      }
    }

    if (capabilityFilter.length > 0) {
      if (!capabilityFilter.some((c) => fam.capabilities.includes(c))) {
        return false;
      }
    }

    if (sizeFilter) {
      const params = fam.param_range[1] ?? 0;
      if (sizeFilter === "small" && params >= 4) return false;
      if (sizeFilter === "medium" && (params < 4 || params > 14)) return false;
      if (sizeFilter === "large" && params <= 14) return false;
    }

    return true;
  });

  // Sort
  if (sort !== "relevance") {
    filteredFamilies = [...filteredFamilies].sort((a, b) => {
      if (sort === "size_asc") return (a.default_variant.size_bytes ?? 0) - (b.default_variant.size_bytes ?? 0);
      if (sort === "size_desc") return (b.default_variant.size_bytes ?? 0) - (a.default_variant.size_bytes ?? 0);
      if (sort === "params_asc") return (a.param_range[1] ?? 0) - (b.param_range[1] ?? 0);
      if (sort === "params_desc") return (b.param_range[1] ?? 0) - (a.param_range[1] ?? 0);
      return 0;
    });
  }

  const capabilities = ["chat", "code", "vision"];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <Input
            label="Search models"
            placeholder="Search by name, family..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-1.5">
          {capabilities.map((cap) => (
            <button
              key={cap}
              onClick={() =>
                setCapabilityFilter((prev) =>
                  prev.includes(cap) ? prev.filter((c) => c !== cap) : [...prev, cap]
                )
              }
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

        <div className="flex items-center gap-1.5">
          {(["small", "medium", "large"] as const).map((size) => (
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

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="h-9 rounded-md border border-border-default bg-bg-surface px-2.5 text-xs text-text-secondary"
          aria-label="Sort families"
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
        {filteredFamilies.length} families · {data.total_models} models
      </p>

      {/* Families grid */}
      {filteredFamilies.length > 0 ? (
        <div className="space-y-4">
          {filteredFamilies.map((fam) => (
            <FamilyCard
              key={fam.family}
              family={fam}
              ram_gb={ram_gb}
              onDownload={onDownload}
              onViewDetail={onViewDetail}
              onToggleCompare={onToggleCompare}
              compareSelectedIds={compareSelectedIds}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No families found"
          description={searchQuery ? "Try a different search query or filters" : "No models available"}
        />
      )}

      {/* Embedding models section */}
      <EmbeddingSection
        families={data.embedding_families}
        onDownload={onDownload}
        onViewDetail={onViewDetail}
      />
    </div>
  );
}
