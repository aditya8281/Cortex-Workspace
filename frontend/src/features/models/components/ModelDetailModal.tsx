"use client";

import { useState, useEffect } from "react";
import { Modal } from "@/shared/ui/Modal";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { FamilySummary, FamilyVariant, FamilyVariantsResponse, HardwareInfo } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { formatParamCount, calculateRamFit } from "@/features/models/api";
import { VariantRow } from "./VariantRow";

interface ModelDetailModalProps {
  family: FamilySummary | null;
  open: boolean;
  onClose: () => void;
  onDownload: (modelId: string) => void;
  onUseInChat: (modelId: string) => void;
  onSetDefault: (modelId: string) => void;
  hardware: HardwareInfo | null;
  defaultModel: string | null;
}

type SortKey = "size" | "params";

export function ModelDetailModal({
  family: initialFamily,
  open,
  onClose,
  onDownload,
  onUseInChat,
  onSetDefault,
  hardware,
  defaultModel,
}: ModelDetailModalProps) {
  const [variantsData, setVariantsData] = useState<FamilyVariantsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<SortKey>("size");
  const ram_gb = hardware?.ram_gb ?? 32;

  useEffect(() => {
    if (!open || !initialFamily) return;
    setLoading(true);
    catalog
      .familyVariants(initialFamily.family)
      .then(setVariantsData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [open, initialFamily]);

  if (!initialFamily) return null;

  const variants = variantsData?.variants ?? [];
  const isEmbedding = initialFamily.embedding_dim !== null;

  const sortedVariants = [...variants].sort((a, b) => {
    if (sortBy === "size") return (a.size_bytes ?? 0) - (b.size_bytes ?? 0);
    return (b.parameter_count ?? 0) - (a.parameter_count ?? 0);
  });

  return (
    <Modal open={open} onClose={onClose}>
      <div className="max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-border-default/50">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-text-primary">
              {initialFamily.display_name}
            </h2>
            <div className="flex items-center gap-2">
              {initialFamily.license && (
                <Badge variant="default">{initialFamily.license}</Badge>
              )}
            </div>
          </div>
          <p className="text-xs text-text-muted">
            {initialFamily.model_count} variants
          </p>
        </div>

        {/* Overview */}
        <div className="p-6 border-b border-border-default/50">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Overview</h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {isEmbedding ? (
              <>
                <div>
                  <span className="text-text-muted">Dimensions:</span>{" "}
                  <span className="text-text-primary">{initialFamily.embedding_dim}</span>
                </div>
                <div>
                  <span className="text-text-muted">Context:</span>{" "}
                  <span className="text-text-primary">
                    {initialFamily.context_range[0] >= 1000
                      ? `${Math.round(initialFamily.context_range[0] / 1000)}K`
                      : initialFamily.context_range[0]}
                  </span>
                </div>
              </>
            ) : (
              <>
                <div>
                  <span className="text-text-muted">Parameters:</span>{" "}
                  <span className="text-text-primary">
                    {formatParamCount(initialFamily.param_range[0])}–
                    {formatParamCount(initialFamily.param_range[1])}
                  </span>
                </div>
                <div>
                  <span className="text-text-muted">Context:</span>{" "}
                  <span className="text-text-primary">
                    {initialFamily.context_range[0] >= 1000
                      ? `${Math.round(initialFamily.context_range[0] / 1000)}K`
                      : initialFamily.context_range[0]}–
                    {initialFamily.context_range[1] >= 1000
                      ? `${Math.round(initialFamily.context_range[1] / 1000)}K`
                      : initialFamily.context_range[1]}
                  </span>
                </div>
              </>
            )}
            <div className="col-span-2">
              <span className="text-text-muted">Capabilities:</span>{" "}
              <div className="flex gap-1 mt-1">
                {initialFamily.capabilities.map((cap) => (
                  <Badge key={cap} variant="default">{cap}</Badge>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Variants table */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              Variants ({variants.length})
            </h3>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setSortBy("size")}
                className={`px-2 py-1 rounded text-xs motion-safe:transition-colors ${
                  sortBy === "size" ? "bg-accent/12 text-accent" : "text-text-muted hover:text-text-secondary"
                }`}
              >
                Size
              </button>
              <button
                onClick={() => setSortBy("params")}
                className={`px-2 py-1 rounded text-xs motion-safe:transition-colors ${
                  sortBy === "params" ? "bg-accent/12 text-accent" : "text-text-muted hover:text-text-secondary"
                }`}
              >
                Params
              </button>
            </div>
          </div>

          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : sortedVariants.length > 0 ? (
            <div className="border border-border-default/50 rounded-lg overflow-hidden">
              {sortedVariants.map((v) => {
                const minRam = v.size_gb ? v.size_gb * 1.2 : 0;
                const fit = calculateRamFit(ram_gb, minRam);
                return (
                  <VariantRow
                    key={v.model_id}
                    variant={v}
                    ramFitPercent={fit.percent}
                    ramFitStatus={fit.status}
                    onDownload={onDownload}
                  />
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-text-muted">No variants available</p>
          )}
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-border-default/50 flex items-center gap-3">
          <Button onClick={() => onUseInChat(initialFamily.default_variant.model_id)}>
            Use in Chat
          </Button>
          {initialFamily.default_variant.model_id !== defaultModel && (
            <Button
              variant="ghost"
              onClick={() => onSetDefault(initialFamily.default_variant.model_id)}
            >
              Set as Default
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
