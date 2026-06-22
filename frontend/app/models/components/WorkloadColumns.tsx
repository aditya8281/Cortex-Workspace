"use client";

import { MessageSquare, Code, Eye, Cpu, ArrowDownToLine } from "lucide-react";
import type { WorkloadRecommendations } from "@/shared/types";

interface WorkloadColumnsProps {
  workloads: Record<string, WorkloadRecommendations>;
  onDownload: (modelId: string, variant?: string) => void;
}

const WORKLOAD_ICONS: Record<string, typeof MessageSquare> = {
  chat: MessageSquare,
  coding: Code,
  code: Code,
  vision: Eye,
  reasoning: Cpu,
  agents: Cpu,
};

export default function WorkloadColumns({ workloads, onDownload }: WorkloadColumnsProps) {
  const entries = Object.entries(workloads);
  if (entries.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted mb-3 flex items-center gap-2">
        By workload
        <span className="flex-1 h-px bg-white/[0.06]" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {entries.map(([key, wl]) => {
          const Icon = WORKLOAD_ICONS[key] || Cpu;
          return (
            <div key={key} className="glass-panel rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-white/[0.06] flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center">
                  <Icon size={14} className="text-accent" />
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-primary">{wl.label}</div>
                  <div className="text-[10px] text-muted">{wl.recommendations.length} models</div>
                </div>
              </div>
              {wl.recommendations.slice(0, 3).map((rec) => {
                const fit = Math.round(rec.score * 100);
                const fitColor = fit >= 75 ? "text-success" : fit >= 60 ? "text-accent" : "text-muted";
                return (
                  <div key={rec.model_id} className="px-4 py-3 border-b border-white/[0.06] last:border-b-0 flex justify-between items-center hover:bg-white/[0.02] transition-colors">
                    <div className="min-w-0">
                      <div className="text-[13px] font-medium text-primary truncate">{rec.display_name}</div>
                      {rec.variant && (
                        <div className="font-mono text-[10px] text-muted mt-0.5">
                          {rec.variant.quantization} · {rec.variant.size_gb} GB
                        </div>
                      )}
                    </div>
                    <div className="text-right ml-3 shrink-0">
                      <div className={`font-mono text-[12px] font-medium ${fitColor}`}>{fit}%</div>
                      {rec.performance && (
                        <div className="font-mono text-[10px] text-muted">{rec.performance.tokens_per_second} t/s</div>
                      )}
                      <button
                        onClick={() => onDownload(rec.model_id, rec.variant?.quantization)}
                        className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 mt-1 rounded-md border border-accent/20 text-accent hover:bg-accent/10 hover:border-accent/40 transition-all"
                        aria-label={`Download ${rec.display_name}`}
                      >
                        <ArrowDownToLine size={10} />
                        Get
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
