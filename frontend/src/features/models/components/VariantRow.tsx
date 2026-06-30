"use client";

import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import type { FamilyVariant } from "@/features/developer/api";
import { formatParamCount } from "@/features/models/api";

interface VariantRowProps {
  variant: FamilyVariant;
  ramFitPercent: number;
  ramFitStatus: "good" | "tight" | "insufficient";
  onDownload?: (modelId: string) => void;
}

export function VariantRow({ variant, ramFitPercent, ramFitStatus, onDownload }: VariantRowProps) {
  const statusColor = {
    good: "bg-accent/20",
    tight: "bg-warning/20",
    insufficient: "bg-danger/20",
  }[ramFitStatus];

  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-border-default/50 last:border-0">
      {/* Name */}
      <span className="text-sm font-medium text-text-primary min-w-[140px] truncate">
        {variant.model_id}
      </span>

      {/* Params */}
      <span className="text-sm text-text-secondary min-w-[60px]">
        {formatParamCount(variant.parameter_count)}
      </span>

      {/* Size */}
      <span className="text-sm text-text-secondary min-w-[80px]">
        {variant.size_gb ? `${variant.size_gb} GB` : "—"}
      </span>

      {/* Quantization */}
      <span className="text-xs font-mono text-text-muted min-w-[80px]">
        {variant.quantization || "—"}
      </span>

      {/* Context */}
      <span className="text-xs text-text-muted min-w-[60px]">
        {variant.context_length ? `${Math.round(variant.context_length / 1000)}K` : "—"}
      </span>

      {/* RAM fit bar */}
      <div className="flex-1 min-w-[100px]">
        <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
          <div
            className={`h-full rounded-full ${statusColor}`}
            style={{ width: `${Math.min(100, ramFitPercent)}%` }}
          />
        </div>
      </div>

      {/* Action */}
      {variant.downloaded ? (
        <Badge variant="success">Installed</Badge>
      ) : (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onDownload?.(variant.model_id)}
        >
          Download
        </Button>
      )}
    </div>
  );
}
