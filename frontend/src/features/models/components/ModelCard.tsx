"use client";

import type { ModelWithFit, RamFitStatus } from "../api";
import { formatBytes, formatParamCount, formatSpeed } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";

interface ModelCardProps {
  model: ModelWithFit;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelected: boolean;
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
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
}: ModelCardProps) {
  const { state, actions } = useDownloadContext();
  const job = state.active.find(j => j.model_id === model.model_id)
    ?? state.queued.find(j => j.model_id === model.model_id)
    ?? null;
  const downloading = !!job;
  const downloadProgress = job?.progress ?? 0;
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
      {downloading && job && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex-1 h-2 rounded-full bg-bg-surface overflow-hidden">
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
            <span className="text-xs text-text-muted font-mono ml-2 w-10 text-right">
              {Math.round(downloadProgress * 100)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[0.625rem] text-text-muted font-mono">
              {formatSpeed(job.speed_bytes_sec ?? 0)}
            </span>
            <div className="flex items-center gap-1">
              {job.status === "downloading" ? (
                <button
                  onClick={() => actions.pause(job.job_id)}
                  className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-surface transition-colors"
                  aria-label={`Pause download of ${model.display_name}`}
                  title="Pause"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                    <rect x="2.5" y="1.5" width="2.5" height="9" rx="0.5" />
                    <rect x="7" y="1.5" width="2.5" height="9" rx="0.5" />
                  </svg>
                </button>
              ) : job.status === "paused" ? (
                <button
                  onClick={() => actions.resume(job.job_id)}
                  className="p-1 rounded text-text-muted hover:text-accent hover:bg-bg-surface transition-colors"
                  aria-label={`Resume download of ${model.display_name}`}
                  title="Resume"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                    <path d="M2.5 1.5v9l7.5-4.5z" />
                  </svg>
                </button>
              ) : null}
              <button
                onClick={() => actions.cancel(model.model_id)}
                className="p-1 rounded text-text-muted hover:text-danger hover:bg-bg-surface transition-colors"
                aria-label={`Cancel download of ${model.display_name}`}
                title="Cancel"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M2.5 2.5l7 7M9.5 2.5l-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-auto pt-1">
        {downloading ? (
          <span className="text-xs text-text-muted font-mono">
            {job?.status === "queued" ? "Queued" : "Downloading"}
          </span>
        ) : model.downloaded ? (
          <>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onViewDetail(model.model_id)}
            >
              View Details
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => actions.deleteLocal(model.model_id)}
              className="text-danger hover:text-danger/80"
              aria-label={`Delete ${model.display_name}`}
            >
              Delete
            </Button>
          </>
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
