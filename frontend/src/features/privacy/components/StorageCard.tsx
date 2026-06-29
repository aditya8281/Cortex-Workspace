"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { privacySettings, type StorageUsage } from "../api";

function formatGB(gb: number): string {
  return `${gb.toFixed(1)} GB`;
}

export function StorageCard() {
  const [data, setData] = useState<StorageUsage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await privacySettings.storage();
        if (!cancelled) setData(res);
      } catch {
        // silently fail — component shows fallback
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const usagePct =
    data && data.total_disk_gb > 0
      ? (data.used_disk_gb / data.total_disk_gb) * 100
      : 0;

  return (
    <Card>
      <h3 className="text-sm font-semibold text-text-primary mb-3">Storage</h3>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-4 w-20" />
        </div>
      ) : data ? (
        <>
          <div className="mb-3">
            <p className="text-xs text-text-muted">Disk Usage</p>
            <p className="text-lg font-semibold text-text-primary tabular-nums">
              {formatGB(data.used_disk_gb)}{" "}
              <span className="text-xs font-normal text-text-muted">
                of {formatGB(data.total_disk_gb)}
              </span>
            </p>
          </div>

          {/* Disk usage bar */}
          <div className="h-2 w-full overflow-hidden rounded-full bg-bg-surface mb-3">
            <div
              className="h-full rounded-full bg-accent transition-[width] duration-300"
              style={{ width: `${Math.min(usagePct, 100)}%` }}
            />
          </div>

          <div className="space-y-2">
            {/* Free space */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary">Free</span>
              <span className="text-xs text-text-muted tabular-nums">
                {formatGB(data.free_disk_gb)}
              </span>
            </div>

            {/* Models size */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary">Models</span>
              <span className="text-xs text-text-muted tabular-nums">
                {formatGB(data.models_total_gb)}
              </span>
            </div>

            {/* Cache */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary">Cache</span>
              <span className="text-xs text-text-muted tabular-nums">
                {formatGB(data.cache_gb)}
              </span>
            </div>
          </div>

          {/* Models breakdown */}
          {data.models && data.models.length > 0 && (
            <div className="mt-3 border-t border-border-subtle pt-3">
              <p className="mb-1 block text-xs text-text-muted">
                Installed models
              </p>
              <div className="space-y-1">
                {data.models.map((model) => (
                  <div key={model.name} className="flex items-center justify-between">
                    <span className="text-xs text-text-secondary truncate mr-2">
                      {model.name}
                    </span>
                    <span className="text-xs text-text-muted tabular-nums shrink-0">
                      {formatGB(model.size_gb)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-xs text-text-muted">Unable to load storage data</p>
      )}
    </Card>
  );
}
