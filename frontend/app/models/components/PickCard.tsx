"use client";

import type { ModelRecommendation } from "@/shared/types";

interface PickCardProps {
  recommendation: ModelRecommendation;
  isActive: boolean;
  onDownload: (modelId: string, variant?: string) => void;
}

export default function PickCard({ recommendation: rec, isActive, onDownload }: PickCardProps) {
  const fitPercent = Math.round(rec.score * 100);
  const variant = rec.variant;
  const perf = rec.performance;

  return (
    <div
      className={`min-w-[320px] max-w-[320px] rounded-xl border p-5 transition-all duration-300 ${
        isActive
          ? "border-accent bg-elevated shadow-[0_0_20px_rgba(14,165,201,0.15)] scale-[1.02]"
          : "border-white/[0.06] bg-elevated opacity-70"
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="font-mono text-[10px] text-muted uppercase">#{rec.score > 0.8 ? "Best" : "Top pick"}</div>
          <div className="text-[17px] font-semibold mt-1">{rec.display_name}</div>
          <div className="text-[12px] text-secondary mt-0.5">
            {rec.family} · {rec.parameter_count}
          </div>
        </div>
        <div className="font-mono text-[20px] font-bold text-accent-bright">{fitPercent}%</div>
      </div>

      {perf && (
        <div className="flex gap-4 text-[12px] text-secondary mb-3">
          <span><span className="text-primary font-medium">{perf.tokens_per_second}</span> t/s</span>
          <span><span className="text-primary font-medium">{variant?.size_gb}</span> GB</span>
          <span><span className="text-primary font-medium">{variant?.vram_required_gb}</span> GB VRAM</span>
        </div>
      )}

      <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden mb-3">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent to-accent-bright"
          style={{ width: `${fitPercent}%` }}
        />
      </div>

      {rec.explanation?.why && (
        <p className="text-[12px] text-muted italic mb-4 line-clamp-2">&ldquo;{rec.explanation.why}&rdquo;</p>
      )}

      {isActive && variant && (
        <div className="flex gap-1.5 mb-4">
          {["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"].map((q) => (
            <button
              key={q}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-md border transition-colors ${
                q === variant.quantization
                  ? "border-accent text-accent bg-accent/5"
                  : "border-white/[0.06] text-muted bg-surface hover:border-white/[0.1] hover:text-primary"
              }`}
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onDownload(rec.model_id, variant?.quantization)}
          className="text-[12px] font-medium px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-bright transition-colors"
        >
          Download
        </button>
        <button className="text-[12px] font-medium px-4 py-2 rounded-lg border border-white/[0.1] text-secondary hover:border-accent hover:text-primary transition-colors">
          Details →
        </button>
      </div>
    </div>
  );
}
