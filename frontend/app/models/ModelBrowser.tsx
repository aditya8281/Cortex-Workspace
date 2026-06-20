"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Filter } from "lucide-react";
import ModelCard from "./ModelCard";
import Skeleton from "@/shared/ui/Skeleton";
import { modelsApi } from "@/shared/api";
import type { ModelInfo, HardwareInfo } from "@/shared/types";

const MODEL_TYPES = ["all", "chat", "code", "vision", "embedding"] as const;
type FilterType = (typeof MODEL_TYPES)[number];

interface ModelBrowserProps {
  onModelSelect?: (model: ModelInfo) => void;
}

export default function ModelBrowser({ onModelSelect }: ModelBrowserProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());

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

  // Poll download progress
  useEffect(() => {
    if (downloadingModels.size === 0) return;

    const interval = setInterval(async () => {
      for (const modelName of downloadingModels) {
        try {
          const res = await modelsApi.progress(modelName);
          setDownloadProgress((prev) => new Map(prev).set(modelName, res.progress));
          if (res.progress >= 1.0) {
            setDownloadingModels((prev) => {
              const next = new Set(prev);
              next.delete(modelName);
              return next;
            });
            // Refresh model list to mark as downloaded
            fetchData();
          }
        } catch {
          // Stop polling on error
          setDownloadingModels((prev) => {
            const next = new Set(prev);
            next.delete(modelName);
            return next;
          });
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [downloadingModels, fetchData]);

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

    return matchesSearch && matchesFilter;
  });

  const modelCounts = {
    all: models.length,
    chat: models.filter((m) => m.model_type === "chat").length,
    code: models.filter((m) => m.model_type === "code").length,
    vision: models.filter((m) => m.model_type === "vision").length,
    embedding: models.filter((m) => m.model_type === "embedding").length,
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
        {/* Search */}
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 pl-10 pr-4 rounded-xl bg-bg-surface border border-border-subtle
                       text-sm text-text placeholder:text-text-muted
                       focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20
                       transition-colors"
          />
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
