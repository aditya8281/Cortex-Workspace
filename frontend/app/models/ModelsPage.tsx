"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  Code,
  Eye,
  Wrench,
  Database,
  Zap,
  Star,
  Search,
  RefreshCw,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import Card from "@/shared/ui/Card";
import Button from "@/shared/ui/Button";
import HardwareBar from "./components/HardwareBar";
import SearchBar from "./components/SearchBar";
import RecommendedRow from "./components/RecommendedRow";
import CategorySection from "./components/CategorySection";
import { useAuth } from "@/shared/auth/AuthProvider";
import { modelsApi } from "@/shared/api";
import { useSystemWebSocket } from "@/shared/hooks/useSystemWebSocket";
import type {
  HardwareProfile,
  WorkloadRecommendations as WorkloadRecs,
  ModelInfo,
  ModelRecommendation,
} from "@/shared/types";

const workloadIcons: Record<string, typeof Brain> = {
  coding: Code,
  reasoning: Brain,
  agents: Wrench,
  vision: Eye,
  embeddings: Database,
  lightweight: Zap,
  high_quality: Star,
  rag: Search,
};

function matchesSizeFilter(parameterCount: string, filter: string): boolean {
  if (filter === "all") return true;
  const match = parameterCount.match(/([\d.]+)\s*[Bb]/i);
  if (!match) return false;
  const bn = parseFloat(match[1]);
  switch (filter) {
    case "<3B":
      return bn < 3;
    case "3-8B":
      return bn >= 3 && bn <= 8;
    case "8-14B":
      return bn > 8 && bn <= 14;
    case "14B+":
      return bn > 14;
    default:
      return true;
  }
}

function recommendationToModelInfo(rec: ModelRecommendation): ModelInfo {
  return {
    model_id: rec.model_id,
    name: rec.model_id,
    display_name: rec.display_name,
    description: rec.description,
    provider: "",
    model_type: "chat",
    parameter_count: String(rec.parameter_count),
    context_length: rec.performance?.context_length_max ?? 0,
    capabilities: rec.capabilities,
    hardware_requirements: rec.variant
      ? {
          min_ram_gb: rec.variant.size_gb,
          recommended_ram_gb: rec.variant.size_gb * 1.5,
          min_vram_gb: rec.variant.vram_required_gb,
          recommended_vram_gb: rec.variant.vram_required_gb * 1.2,
        }
      : null,
    family: rec.family,
    architecture: "",
    license: "",
  };
}

export default function ModelsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [workloads, setWorkloads] = useState<Record<string, WorkloadRecs>>({});
  const [allModels, setAllModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());

  const [searchQuery, setSearchQuery] = useState("");
  const [activeTypeFilter, setActiveTypeFilter] = useState("all");
  const [activeSizeFilter, setActiveSizeFilter] = useState("all");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [compareModels, setCompareModels] = useState<string[]>([]);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  const fetchData = useCallback(async () => {
    if (!user) return;
    try {
      const [recsData, listData] = await Promise.all([
        modelsApi.recommendedEnhanced(),
        modelsApi.list(),
      ]);
      setHardware(recsData.hardware);
      setWorkloads(recsData.workloads);
      setAllModels(listData.models);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load models");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await modelsApi.autocomplete(searchQuery);
        setSuggestions(res.suggestions);
      } catch {
        setSuggestions([]);
      }
    }, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const handleDownload = async (modelName: string, variant?: string) => {
    try {
      const res = await modelsApi.download(modelName, variant);
      const key = res.download_id || modelName;
      setDownloadingModels((prev) => new Set(prev).add(key));
      setDownloadProgress((prev) => new Map(prev).set(key, 0));
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  const handleCancel = async (modelName: string) => {
    try {
      await modelsApi.cancel(modelName);
      setDownloadingModels((prev) => {
        const n = new Set(prev);
        n.delete(modelName);
        return n;
      });
      setDownloadProgress((prev) => {
        const n = new Map(prev);
        n.delete(modelName);
        return n;
      });
    } catch (err) {
      console.error("Cancel failed:", err);
    }
  };

  useSystemWebSocket({
    path: "/ws/models",
    enabled: downloadingModels.size > 0,
    onMessage(event) {
      const data = JSON.parse(event.data);
      if (data.type === "model_progress" && Array.isArray(data.models)) {
        for (const m of data.models) {
          setDownloadProgress((prev) => new Map(prev).set(m.name, m.progress));
          if (m.progress >= 1.0) {
            setDownloadingModels((prev) => {
              const n = new Set(prev);
              n.delete(m.name);
              return n;
            });
            fetchData();
          }
        }
      }
    },
  });

  const topRecs = useMemo(() => {
    const all = Object.values(workloads).flatMap((w) => w.recommendations);
    return all.sort((a, b) => b.score - a.score).slice(0, 5);
  }, [workloads]);

  const filteredModels = useMemo(() => {
    return allModels.filter((m) => {
      if (activeTypeFilter !== "all" && m.model_type !== activeTypeFilter) return false;
      if (activeSizeFilter !== "all" && !matchesSizeFilter(m.parameter_count, activeSizeFilter)) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          m.name.toLowerCase().includes(q) ||
          m.display_name.toLowerCase().includes(q) ||
          m.description.toLowerCase().includes(q) ||
          m.family.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [allModels, activeTypeFilter, activeSizeFilter, searchQuery]);

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const m of allModels) {
      counts[m.model_type] = (counts[m.model_type] || 0) + 1;
    }
    return counts;
  }, [allModels]);

  const sizeCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: allModels.length,
      "<3B": 0,
      "3-8B": 0,
      "8-14B": 0,
      "14B+": 0,
    };
    for (const m of allModels) {
      if (matchesSizeFilter(m.parameter_count, "<3B")) counts["<3B"]++;
      if (matchesSizeFilter(m.parameter_count, "3-8B")) counts["3-8B"]++;
      if (matchesSizeFilter(m.parameter_count, "8-14B")) counts["8-14B"]++;
      if (matchesSizeFilter(m.parameter_count, "14B+")) counts["14B+"]++;
    }
    return counts;
  }, [allModels]);

  const categoryModels = useMemo(() => {
    const result: Record<string, ModelInfo[]> = {};
    for (const [id, workload] of Object.entries(workloads)) {
      const recModelIds = new Set(workload.recommendations.map((r) => r.model_id));
      const recModels = filteredModels.filter((m) => recModelIds.has(m.model_id));
      if (recModels.length > 0) {
        result[id] = recModels;
      } else {
        result[id] = workload.recommendations.map(recommendationToModelInfo);
      }
    }
    return result;
  }, [workloads, filteredModels]);

  if (authLoading || !user) return null;

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-6"
        >
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
              <Brain size={24} className="text-accent" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-text">Models</h1>
              <p className="text-sm text-text-secondary">
                Browse, download, and manage LLM models for your agents
              </p>
            </div>
          </div>
        </motion.div>

        {/* Hardware Status Bar */}
        {hardware && (
          <HardwareBar hardware={hardware} activeDownloads={downloadingModels.size} />
        )}

        {/* Loading State */}
        {loading && (
          <div className="space-y-6 mt-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <div className="h-6 w-48 rounded bg-bg-surface shimmer-bg" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <div key={j} className="h-48 rounded-xl bg-bg-surface shimmer-bg" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <Card className="p-8 text-center mt-6">
            <p className="text-sm text-text-secondary mb-4">{error}</p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setError(null);
                setLoading(true);
                fetchData();
              }}
            >
              <RefreshCw size={14} /> Retry
            </Button>
          </Card>
        )}

        {/* Main Content */}
        {!loading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.15 }}
            className="space-y-8 mt-6"
          >
            {/* Search + Filters */}
            <SearchBar
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onSearchSubmit={() => {}}
              activeTypeFilter={activeTypeFilter}
              onTypeFilterChange={setActiveTypeFilter}
              activeSizeFilter={activeSizeFilter}
              onSizeFilterChange={setActiveSizeFilter}
              typeCounts={typeCounts}
              sizeCounts={sizeCounts}
              suggestions={suggestions}
              onSuggestionSelect={(s) => {
                setSearchQuery(s);
              }}
              onCompare={() => {
                if (compareModels.length > 0) {
                  router.push(`/models/compare?ids=${compareModels.join(",")}`);
                }
              }}
              compareCount={compareModels.length}
            />

            {/* Recommended Row */}
            {topRecs.length > 0 && (
              <RecommendedRow
                recommendations={topRecs}
                hardware={hardware}
                onDownload={handleDownload}
              />
            )}

            {/* Category Sections */}
            {Object.entries(workloads).map(([id, workload]) => {
              const Icon = workloadIcons[id] || Brain;
              const models = categoryModels[id] || [];
              return (
                <CategorySection
                  key={id}
                  icon={<Icon size={16} />}
                  title={workload.label}
                  count={workload.recommendations.length}
                  models={models}
                  hardware={hardware}
                  onDownload={handleDownload}
                  onCancel={handleCancel}
                  downloadProgress={downloadProgress}
                  downloadingModels={downloadingModels}
                />
              );
            })}

            {/* All Models Fallback (when no workloads match filters) */}
            {Object.keys(categoryModels).length === 0 && filteredModels.length > 0 && (
              <CategorySection
                icon={<Search size={16} />}
                title="All Models"
                count={filteredModels.length}
                models={filteredModels}
                hardware={hardware}
                onDownload={handleDownload}
                onCancel={handleCancel}
                downloadProgress={downloadProgress}
                downloadingModels={downloadingModels}
              />
            )}
          </motion.div>
        )}
      </div>
    </DashboardShell>
  );
}
