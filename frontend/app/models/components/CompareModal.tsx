"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Trophy, Download, AlertCircle } from "lucide-react";
import Button from "@/shared/ui/Button";
import Badge from "@/shared/ui/Badge";
import Skeleton from "@/shared/ui/Skeleton";
import Modal from "@/shared/ui/Modal";
import { modelsApi } from "@/shared/api";
import { cn } from "@/lib/utils";
import type { ModelComparisonResult, ModelInfo } from "@/shared/types";

interface CompareModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelIds: string[];
}

export default function CompareModal({ isOpen, onClose, modelIds }: CompareModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ModelComparisonResult | null>(null);
  const [modelInfo, setModelInfo] = useState<Record<string, ModelInfo>>({});

  useEffect(() => {
    if (!isOpen || modelIds.length < 2) return;

    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const [comparison, ...details] = await Promise.all([
          modelsApi.compare(modelIds),
          ...modelIds.map((id) => modelsApi.detail(id).catch(() => null)),
        ]);

        if (cancelled) return;

        setResult(comparison);

        const infoMap: Record<string, ModelInfo> = {};
        details.forEach((detail, i) => {
          if (detail) {
            infoMap[modelIds[i]] = detail as unknown as ModelInfo;
          }
        });
        setModelInfo(infoMap);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load comparison data");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [isOpen, modelIds]);

  function formatValue(value: number, dimension: string): string {
    if (dimension === "context_length") {
      if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
      if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
      return String(value);
    }
    if (dimension === "vram_required" || dimension === "size_gb") {
      return `${value.toFixed(1)} GB`;
    }
    if (dimension === "quality_score") {
      return `${value.toFixed(1)}/10`;
    }
    if (dimension === "estimated_tps") {
      return `${value.toFixed(0)} tok/s`;
    }
    return String(value);
  }

  function getDisplayName(modelId: string): string {
    if (modelInfo[modelId]) {
      const info = modelInfo[modelId];
      return info.display_name || info.name || modelId;
    }
    return modelId;
  }

  function getDisplayNames(): string[] {
    return modelIds.map(getDisplayName);
  }

  return (
    <Modal open={isOpen} onOpenChange={onClose}>
      <div className="min-w-[600px] max-w-[900px]">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-text font-display">
              Model Comparison
            </h2>
            {modelIds.length > 0 && (
              <Badge variant="accent">
                {modelIds.length} models
              </Badge>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="max-h-[70vh] overflow-auto -mx-6 px-6">
          {loading && (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {error && (
            <div className="flex items-center gap-3 rounded-xl bg-error/10 border border-error/20 px-4 py-3">
              <AlertCircle className="h-4 w-4 text-error shrink-0" />
              <p className="text-sm text-error">{error}</p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              {/* Overall Winner */}
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3 rounded-xl bg-success/10 border border-success/20 px-4 py-3"
              >
                <Trophy className="h-5 w-5 text-success shrink-0" />
                <div>
                  <p className="text-sm font-medium text-text">
                    Overall Winner: {getDisplayName(result.winner_model)}
                  </p>
                  {result.summary && (
                    <p className="text-xs text-text-secondary mt-0.5">{result.summary}</p>
                  )}
                </div>
              </motion.div>

              {/* Comparison Table */}
              <div className="rounded-xl border border-border-subtle overflow-hidden">
                {/* Table Header */}
                <div
                  className="grid border-b border-border-subtle"
                  style={{
                    gridTemplateColumns: `180px repeat(${modelIds.length}, 1fr)`,
                  }}
                >
                  <div className="px-4 py-3 bg-bg-surface text-xs font-medium text-text-muted uppercase tracking-wider">
                    Dimension
                  </div>
                  {modelIds.map((id) => (
                    <div
                      key={id}
                      className={cn(
                        "px-4 py-3 bg-bg-surface text-xs font-medium text-text-secondary truncate",
                        id === result.winner_model && "text-success"
                      )}
                    >
                      <span className="truncate block">{getDisplayName(id)}</span>
                    </div>
                  ))}
                </div>

                {/* Table Rows */}
                {result.dimensions.map((dim, idx) => {
                  const winCount = result.dimension_wins[dim.dimension] || "";
                  return (
                    <motion.div
                      key={dim.dimension}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.05 }}
                      className="grid border-b border-border-subtle last:border-b-0"
                      style={{
                        gridTemplateColumns: `180px repeat(${modelIds.length}, 1fr)`,
                      }}
                    >
                      <div className="px-4 py-3 bg-bg-surface/50 text-xs text-text-secondary font-medium">
                        {dim.display_name}
                      </div>
                      {modelIds.map((id) => {
                        const value = dim.values[id];
                        const isWinner = dim.winner === id;
                        return (
                          <div
                            key={id}
                            className={cn(
                              "px-4 py-3 text-sm font-mono",
                              isWinner && "bg-success/10 text-success font-medium",
                              !isWinner && "text-text-secondary"
                            )}
                          >
                            {value != null ? formatValue(value, dim.dimension) : "—"}
                          </div>
                        );
                      })}
                    </motion.div>
                  );
                })}
              </div>

              {/* Download Actions */}
              <div
                className="grid gap-3"
                style={{
                  gridTemplateColumns: `repeat(${modelIds.length}, 1fr)`,
                }}
              >
                {modelIds.map((id) => (
                  <div key={id} className="flex flex-col items-center gap-1">
                    <span className="text-[11px] text-text-muted truncate w-full text-center">
                      {getDisplayName(id)}
                    </span>
                    <Button
                      variant="secondary"
                      size="sm"
                      className="w-full"
                      onClick={() => {
                        window.location.href = `/models/${id}`;
                      }}
                    >
                      <Download className="h-3.5 w-3.5" />
                      View Details
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
