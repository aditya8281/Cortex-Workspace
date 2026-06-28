"use client";

import type { ModelWithFit, RamFitStatus } from "../api";
import { formatBytes, formatParamCount } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";

interface ModelCardProps {
  model: ModelWithFit;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelected: boolean;
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
  downloading?: boolean;
  downloadProgress?: number;
  onCancelDownload?: (modelId: string) => void;
}

const fitColors: Record<RamFitStatus, string> = {
  good: "bg-success",
  tight: "bg-warning",
  insufficient: "bg-danger",
};

const fitLabels: Record<RamFitStatus, string> = {
  good: "Good fit",
  tight: "Tight",
  insufficient: "Low RAM",
};

export function ModelCard({
  model,
  onDownload,
  onViewDetail,
  compareSelected,
  onToggleCompare,
  compareDisabled,
  downloading,
  downloadProgress,
  onCancelDownload,
}: ModelCardProps) {
  const primaryVariant = model.variants?.[0];
  const minRam = model.hardware_requirements?.min_ram_gb ?? null;

  return (
    <Card className="p-4 flex flex-col gap-3" role="article" aria-label={model.display_name}>
      {/* Header: name + badges */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-title font-semibold text-text-primary leading-tight">
          {model.display_name}
        </h3>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {model.downloaded && (
            <Badge variant="success">Installed</Badge>
          )}
        </div>
      </div>

      {/* Params + capabilities */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-text-secondary font-mono">
          {formatParamCount(model.parameter_count)} params
        </span>
        {model.capabilities?.map((cap) => (
          <Badge key={cap} variant="default">
            {cap}
          </Badge>
        ))}
      </div>

      {/* Size + variant */}
      {primaryVariant && (
        <p className="text-xs text-text-muted">
          {formatBytes(primaryVariant.size_bytes ?? 0)} · {primaryVariant.quantization}
        </p>
      )}

      {/* RAM fit */}
      {minRam && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">
            RAM: {minRam}GB needed
          </span>
        </div>
      )}

      {minRam && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-bg-surface overflow-hidden">
            <div
              className={`h-full rounded-full ${fitColors[model.ramFitStatus]}`}
              style={{ width: `${model.ramFitPercent}%` }}
              role="progressbar"
              aria-valuenow={model.ramFitPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${model.ramFitPercent}% RAM fit`}
            />
          </div>
          <span className="text-[0.625rem] text-text-muted font-mono w-12 text-right">
            {model.ramFitPercent}%
          </span>
        </div>
      )}

      {/* Downloading state */}
      {downloading && downloadProgress !== undefined && (
        <div className="space-y-1.5">
          <div className="h-2 rounded-full bg-bg-surface overflow-hidden">
            <div
              className="h-full rounded-full bg-accent transition-[width] duration-300"
              style={{ width: `${Math.round(downloadProgress * 100)}%` }}
              role="progressbar"
              aria-valuenow={Math.round(downloadProgress * 100)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Downloading ${model.display_name}: ${Math.round(downloadProgress * 100)}%`}
            />
          </div>
          <span className="text-xs text-text-muted">
            {Math.round(downloadProgress * 100)}%
          </span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-auto pt-1">
        {downloading ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onCancelDownload?.(model.model_id)}
            aria-label={`Cancel download of ${model.display_name}`}
          >
            Cancel
          </Button>
        ) : model.downloaded ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onViewDetail(model.model_id)}
          >
            View Details
          </Button>
        ) : (
          <Button
            size="sm"
            onClick={() => onDownload(model.model_id)}
            aria-label={`Download ${model.display_name}`}
          >
            Download
          </Button>
        )}

        <label className="flex items-center gap-1.5 ml-auto cursor-pointer">
          <input
            type="checkbox"
            checked={compareSelected}
            onChange={() => onToggleCompare(model.model_id)}
            disabled={!compareSelected && compareDisabled}
            className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface text-accent accent-accent"
            aria-label={`Add ${model.display_name} to comparison`}
          />
          <span className="text-xs text-text-muted">Compare</span>
        </label>
      </div>
    </Card>
  );
}
