"use client";

import { motion } from "framer-motion";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import { Zap, TrendingUp, Tag } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ModelRecommendation, HardwareProfile } from "@/shared/types";

interface RecommendedRowProps {
  recommendations: ModelRecommendation[];
  hardware?: HardwareProfile | null;
  onDownload?: (modelId: string) => void;
}

export default function RecommendedRow({ recommendations, hardware, onDownload }: RecommendedRowProps) {
  if (recommendations.length === 0) return null;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2.5">
        <TrendingUp className="h-4 w-4 text-accent" />
        <h2 className="text-sm font-medium text-text">Recommended for Your Hardware</h2>
        <span className="micro-label text-text-muted">{recommendations.length}</span>
      </div>

      {/* Horizontal scroll */}
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-border-subtle scrollbar-track-transparent">
        {recommendations.map((rec, index) => {
          const isBestMatch = index === 0;
          const perf = rec.performance;
          const variant = rec.variant;

          return (
            <motion.div
              key={rec.model_id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className={cn(
                "flex flex-col gap-2.5 p-4 rounded-xl min-w-[280px] max-w-[280px] shrink-0",
                "bg-bg-elevated border transition-all duration-200",
                isBestMatch
                  ? "border-accent/30 shadow-[0_0_20px_rgba(14,165,201,0.08)]"
                  : "border-border-subtle hover:border-accent/15"
              )}
            >
              {/* Top row: Best Match badge + Score */}
              <div className="flex items-center justify-between">
                {isBestMatch && (
                  <Badge variant="accent">Best Match</Badge>
                )}
                {!isBestMatch && (
                  <Badge variant="default">#{index + 1}</Badge>
                )}
                <span className="font-mono text-[11px] text-text-muted">
                  Score: {(rec.score * 100).toFixed(0)}%
                </span>
              </div>

              {/* Name + Family */}
              <div>
                <h3 className="text-sm font-medium text-text truncate">
                  {rec.display_name}
                </h3>
                <p className="text-[11px] text-text-muted">{rec.family}</p>
              </div>

              {/* Variant Info */}
              {variant && (
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="font-mono text-text-secondary">
                    {variant.quantization}
                  </span>
                  <span className="text-text-muted">·</span>
                  <span className="font-mono text-text-secondary">
                    {variant.size_gb.toFixed(1)}GB
                  </span>
                  <span className="text-text-muted">·</span>
                  <span className="font-mono text-text-secondary">
                    {variant.vram_required_gb}GB VRAM
                  </span>
                </div>
              )}

              {/* Performance */}
              {perf && (
                <div className="flex items-center gap-3 text-[11px]">
                  {perf.tokens_per_second != null && (
                    <span className="flex items-center gap-1 text-accent">
                      <Zap className="h-3 w-3" />
                      <span className="font-mono font-medium">
                        {perf.tokens_per_second.toFixed(1)} TPS
                      </span>
                    </span>
                  )}
                  {perf.fit_rating && (
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium",
                      perf.fit_rating === "excellent" && "bg-success/15 text-success",
                      perf.fit_rating === "good" && "bg-accent/15 text-accent",
                      perf.fit_rating === "tight" && "bg-warning/15 text-warning",
                      perf.fit_rating === "poor" && "bg-error/15 text-error",
                      !["excellent", "good", "tight", "poor"].includes(perf.fit_rating) && "bg-bg-hover text-text-muted"
                    )}>
                      {perf.fit_rating}
                    </span>
                  )}
                </div>
              )}

              {/* Capability Tags */}
              {rec.capabilities.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {rec.capabilities.slice(0, 3).map((cap) => (
                    <span
                      key={cap}
                      className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-bg-hover text-[10px] text-text-muted"
                    >
                      <Tag className="h-2.5 w-2.5" />
                      {cap}
                    </span>
                  ))}
                </div>
              )}

              {/* Description */}
              <p className="text-[11px] text-text-muted line-clamp-2 leading-relaxed">
                {rec.description}
              </p>

              {/* Action */}
              <Button
                variant="primary"
                size="sm"
                className="mt-auto"
                onClick={() => onDownload?.(rec.model_id)}
              >
                Download
              </Button>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
