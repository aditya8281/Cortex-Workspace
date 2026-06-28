"use client";

import { useState, useEffect } from "react";
import type { ModelComparison } from "../api";
import { catalog } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";

interface CompareViewProps {
  selectedIds: string[];
  onClearSelection: () => void;
  onDownloadModel: (modelId: string) => void;
}

export function CompareView({
  selectedIds,
  onClearSelection,
  onDownloadModel,
}: CompareViewProps) {
  const [comparison, setComparison] = useState<ModelComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedIds.length < 2) {
      setComparison(null);
      return;
    }

    setLoading(true);
    setError(null);
    catalog
      .compare(selectedIds)
      .then(setComparison)
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedIds]);

  if (selectedIds.length < 2) {
    return (
      <EmptyState
        title="Select models to compare"
        description="Check the compare checkbox on 2-5 model cards in the Browse tab"
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
        {error}
      </div>
    );
  }

  if (!comparison) return null;

  // Find display names from dimension values
  const modelNames: Record<string, string> = {};
  if (comparison.dimensions.length > 0) {
    const firstDim = comparison.dimensions[0];
    for (const modelId of Object.keys(firstDim.values ?? {})) {
      // Extract name from model_id (e.g., "llama3.1:8b-q4_km" → "Llama3.1 8b")
      modelNames[modelId] = modelId.split(":")[0].replace(/[-_]/g, " ");
    }
  }

  return (
    <div className="space-y-6">
      {/* Model headers */}
      <div className="flex items-center gap-4 flex-wrap">
        {selectedIds.map(id => (
          <span
            key={id}
            className="text-sm font-medium text-text-primary"
          >
            {modelNames[id] ?? id}
          </span>
        ))}
      </div>

      {/* Dimensions */}
      {comparison.dimensions.map(dim => {
        const maxVal = Math.max(
          ...Object.values(dim.values).map(v => (typeof v === "number" ? v : 0))
        );

        return (
          <div key={dim.dimension} className="space-y-2">
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
              {dim.display_name}
            </h4>
            <div className="space-y-1.5">
              {selectedIds.map(id => {
                const val = dim.values[id];
                const numVal = typeof val === "number" ? val : 0;
                const width = maxVal > 0 ? (numVal / maxVal) * 100 : 0;
                const isWinner = dim.winner === id;

                return (
                  <div key={id} className="flex items-center gap-3">
                    <span className="text-xs text-text-secondary w-24 truncate">
                      {modelNames[id] ?? id}
                    </span>
                    <div className="flex-1 h-3 rounded-sm bg-bg-surface overflow-hidden">
                      <div
                        className={`h-full rounded-sm transition-[width] duration-300 ${
                          isWinner ? "bg-accent" : "bg-bg-elevated"
                        }`}
                        style={{ width: `${Math.max(4, width)}%` }}
                      />
                    </div>
                    <span className="text-xs text-text-secondary font-mono w-16 text-right">
                      {typeof val === "number" ? val : String(val)}
                      {isWinner && (
                        <span className="ml-1 text-accent">&#9733;</span>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {/* Winner + actions */}
      {comparison.winner_model && (
        <Card className="p-4">
          <p className="text-sm text-text-secondary mb-1">
            Winner:{" "}
            <span className="font-semibold text-text-primary">
              {modelNames[comparison.winner_model] ?? comparison.winner_model}
            </span>
          </p>
          <p className="text-xs text-text-muted mb-3">{comparison.summary}</p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => onDownloadModel(comparison!.winner_model)}
            >
              Download Winner
            </Button>
            <Button size="sm" variant="ghost" onClick={onClearSelection}>
              Clear Selection
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
