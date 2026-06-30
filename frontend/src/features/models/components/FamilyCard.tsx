"use client";

import { useState, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { FamilySummary, FamilyVariant } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { formatParamCount, calculateRamFit } from "@/features/models/api";
import { VariantRow } from "./VariantRow";

interface FamilyCardProps {
  family: FamilySummary;
  ram_gb: number;
  onDownload?: (modelId: string) => void;
  onViewDetail?: (family: string) => void;
  onToggleCompare?: (modelId: string) => void;
  compareSelectedIds?: string[];
}

export function FamilyCard({
  family,
  ram_gb,
  onDownload,
  onViewDetail,
  onToggleCompare,
  compareSelectedIds = [],
}: FamilyCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [variants, setVariants] = useState<FamilyVariant[]>([]);
  const [loadingVariants, setLoadingVariants] = useState(false);

  const loadVariants = useCallback(async () => {
    if (variants.length > 0) return; // already loaded
    setLoadingVariants(true);
    try {
      const res = await catalog.familyVariants(family.family);
      setVariants(res.variants);
    } catch (e) {
      console.error("Failed to load variants:", e);
    } finally {
      setLoadingVariants(false);
    }
  }, [family.family, variants.length]);

  const handleExpand = async () => {
    if (!expanded) {
      await loadVariants();
    }
    setExpanded(!expanded);
  };

  const dv = family.default_variant;
  const minRam = dv.size_gb ? dv.size_gb * 1.2 : 0;
  const { percent, status } = calculateRamFit(ram_gb, minRam);

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-text-primary">
            {family.display_name}
          </h3>
          <div className="flex items-center gap-2">
            {family.license && (
              <Badge variant="default">{family.license}</Badge>
            )}
            {dv.downloaded && <Badge variant="success">Installed</Badge>}
          </div>
        </div>

        {/* Summary line — clickable to expand */}
        <button
          onClick={handleExpand}
          className="text-xs text-text-muted hover:text-text-secondary transition-colors"
        >
          {expanded ? "▾" : "▸"} {family.model_count} variants ·{" "}
          {formatParamCount(family.param_range[0])}–{formatParamCount(family.param_range[1])} ·{" "}
          {family.context_range[0] >= 1000
            ? `${Math.round(family.context_range[0] / 1000)}K`
            : family.context_range[0]}–
          {family.context_range[1] >= 1000
            ? `${Math.round(family.context_range[1] / 1000)}K`
            : family.context_range[1]} ctx
        </button>

        {/* Capabilities */}
        <div className="flex items-center gap-1.5 mt-2">
          {family.capabilities.map((cap) => (
            <Badge key={cap} variant="default">
              {cap}
            </Badge>
          ))}
        </div>

        {/* Default variant inline */}
        <div className="mt-3 flex items-center gap-3 text-xs">
          <span className="font-medium text-text-primary">{dv.model_id}</span>
          <span className="text-text-secondary">{formatParamCount(dv.parameter_count)}</span>
          <span className="text-text-secondary">{dv.size_gb} GB</span>
          <span className="font-mono text-text-muted">{dv.quantization}</span>
        </div>

        {/* RAM fit bar */}
        <div className="mt-2 h-1.5 rounded-full bg-bg-surface overflow-hidden">
          <div
            className={`h-full rounded-full ${
              status === "good"
                ? "bg-accent"
                : status === "tight"
                ? "bg-warning"
                : "bg-danger"
            }`}
            style={{ width: `${Math.min(100, percent)}%` }}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3">
          {!dv.downloaded && onDownload && (
            <Button size="sm" onClick={() => onDownload(dv.model_id)}>
              Download
            </Button>
          )}
          {onViewDetail && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onViewDetail(family.family)}
            >
              View Details
            </Button>
          )}
        </div>
      </div>

      {/* Expanded variants */}
      {expanded && (
        <div className="border-t border-border-default/50">
          {loadingVariants ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : variants.length > 0 ? (
            variants.map((v) => {
              const vMinRam = v.size_gb ? v.size_gb * 1.2 : 0;
              const vFit = calculateRamFit(ram_gb, vMinRam);
              return (
                <VariantRow
                  key={v.model_id}
                  variant={v}
                  ramFitPercent={vFit.percent}
                  ramFitStatus={vFit.status}
                  onDownload={onDownload}
                />
              );
            })
          ) : (
            <p className="p-4 text-xs text-text-muted">No variants available</p>
          )}
        </div>
      )}
    </Card>
  );
}
