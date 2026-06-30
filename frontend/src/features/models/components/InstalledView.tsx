"use client";

import { useState, useEffect, useCallback } from "react";
import type { FamilySummary, HardwareInfo, ModelFamiliesResponse } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";

interface InstalledViewProps {
  hardware: HardwareInfo | null;
  onDelete: (modelId: string) => void;
  onOpenChat: (modelId: string) => void;
  onSetDefault: (modelId: string) => void;
  defaultModel: string | null;
}

export function InstalledView({
  hardware,
  onDelete,
  onOpenChat,
  onSetDefault,
  defaultModel,
}: InstalledViewProps) {
  const [data, setData] = useState<ModelFamiliesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInstalled = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await catalog.families();
      // Filter to families where default variant is downloaded
      const installedFamilies = result.families.filter(
        (fam) => fam.default_variant.downloaded
      );
      setData({
        ...result,
        families: installedFamilies,
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadInstalled(); }, [loadInstalled]);

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
        {error}
        <Button size="sm" variant="ghost" className="ml-2" onClick={loadInstalled}>
          Retry
        </Button>
      </div>
    );
  }

  if (!data || data.families.length === 0) {
    return (
      <EmptyState
        title="No models installed"
        description="Download a model from the Browse tab to get started"
      />
    );
  }

  // Compute storage summary
  const totalSizeGb = data.families.reduce(
    (acc, fam) => acc + (fam.default_variant.size_gb ?? 0), 0
  );

  return (
    <div className="space-y-6">
      {/* Storage summary */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-text-primary">
            Installed Models
          </h3>
          <span className="text-xs text-text-muted">
            {totalSizeGb.toFixed(1)} GB used
          </span>
        </div>
        <div className="h-2 rounded-full bg-bg-surface overflow-hidden">
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${Math.min(100, (totalSizeGb / 500) * 100)}%` }}
          />
        </div>
        <p className="text-xs text-text-muted mt-1">
          {data.families.length} families · {data.total_models} total models
        </p>
      </Card>

      {/* Installed families */}
      <div className="space-y-4">
        {data.families.map((fam) => (
          <Card key={fam.family} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-text-primary">
                {fam.display_name}
              </h3>
              <div className="flex items-center gap-2">
                {fam.default_variant.model_id === defaultModel && (
                  <Badge variant="success">Default</Badge>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="text-xs text-text-muted mb-3">
              {fam.model_count} variant{fam.model_count !== 1 ? "s" : ""} ·{" "}
              {fam.default_variant.size_gb} GB
            </div>

            {/* Capabilities */}
            <div className="flex items-center gap-1.5 mb-3">
              {fam.capabilities.map((cap) => (
                <Badge key={cap} variant="default">{cap}</Badge>
              ))}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={() => onOpenChat(fam.default_variant.model_id)}
              >
                Open Chat
              </Button>
              {fam.default_variant.model_id !== defaultModel && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSetDefault(fam.default_variant.model_id)}
                >
                  Set Default
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onDelete(fam.default_variant.model_id)}
              >
                Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
