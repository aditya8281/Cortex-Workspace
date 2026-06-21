"use client";

import { motion } from "framer-motion";
import {
  Code,
  Brain,
  Wrench,
  Eye,
  Search,
  Zap,
  Star,
  Database,
} from "lucide-react";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import type { WorkloadRecommendations as WorkloadRecs, ModelRecommendation } from "@/shared/types";

const workloadIcons: Record<string, typeof Code> = {
  coding: Code,
  reasoning: Brain,
  agents: Wrench,
  vision: Eye,
  embeddings: Database,
  lightweight: Zap,
  high_quality: Star,
  rag: Search,
};

const fitColors: Record<string, string> = {
  excellent: "text-success",
  good: "text-accent",
  usable: "text-warning",
  too_large: "text-danger",
};

interface WorkloadRecommendationsProps {
  workloads: Record<string, WorkloadRecs>;
  onDownload?: (modelId: string) => void;
}

export default function WorkloadRecommendations({ workloads, onDownload }: WorkloadRecommendationsProps) {
  return (
    <div className="space-y-8">
      {Object.entries(workloads).map(([workloadId, workload], idx) => {
        if (workload.recommendations.length === 0) return null;
        const Icon = workloadIcons[workloadId] || Star;

        return (
          <motion.div
            key={workloadId}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: idx * 0.05 }}
          >
            {/* Section Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <Icon size={16} className="text-accent" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-text">{workload.label}</h3>
                <p className="text-xs text-text-muted">{workload.description}</p>
              </div>
            </div>

            {/* Recommendation Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {workload.recommendations.slice(0, 3).map((rec, recIdx) => (
                <RecommendationCard key={rec.model_id} rec={rec} rank={recIdx + 1} onDownload={onDownload} />
              ))}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

function RecommendationCard({ rec, rank, onDownload }: { rec: ModelRecommendation; rank: number; onDownload?: (modelId: string) => void }) {
  const perf = rec.performance;
  const variant = rec.variant;

  return (
    <Card className="p-4 h-full flex flex-col relative" gradient>
      {rank === 1 && (
        <div className="absolute top-2 right-2">
          <Badge variant="accent">Best Match</Badge>
        </div>
      )}

      {/* Model name and params */}
      <div className="mb-2">
        <h4 className="text-sm font-semibold text-text">{rec.display_name}</h4>
        <p className="text-xs text-text-muted font-mono">
          {rec.parameter_count ? `${rec.parameter_count}B params` : "Unknown params"}
          {variant && ` · ${variant.quantization} · ${variant.size_gb}GB`}
        </p>
      </div>

      {/* Performance */}
      {perf && (
        <div className="flex flex-wrap gap-3 mb-2 text-xs">
          {perf.tokens_per_second && (
            <span className="flex items-center gap-1">
              <Zap size={10} className="text-accent" />
              ~{perf.tokens_per_second ? Math.round(perf.tokens_per_second) : "–"} tps
            </span>
          )}
          <span className={`flex items-center gap-1 ${fitColors[perf.fit_rating] || "text-text-muted"}`}>
            {perf.fit_rating === "excellent" ? "Excellent fit" :
             perf.fit_rating === "good" ? "Good fit" :
             perf.fit_rating === "usable" ? "Usable" : "Too large"}
          </span>
        </div>
      )}

      {/* Explanation */}
      <p className="text-xs text-text-secondary mb-3 flex-1 line-clamp-3">
        {rec.explanation?.why}
      </p>

      {/* Quality tradeoff */}
      {perf && (
        <p className="text-xs text-text-muted mb-3 italic">
          {perf?.quality_notes}
        </p>
      )}

      {/* Capabilities */}
      <div className="flex flex-wrap gap-1 mb-3">
        {rec.capabilities.slice(0, 4).map((cap) => (
          <Badge key={cap} variant="default" className="text-[10px]">
            {cap}
          </Badge>
        ))}
      </div>

      {/* Action */}
      <div className="mt-auto pt-2 border-t border-border-subtle">
        <Button
          variant="secondary"
          size="sm"
          className="w-full"
          onClick={() => onDownload?.(rec.model_id)}
        >
          Download {variant?.quantization || ""}
        </Button>
      </div>
    </Card>
  );
}
