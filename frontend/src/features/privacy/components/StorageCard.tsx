"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { privacySettings, type StorageUsage } from "../api";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(1)} ${units[i]}`;
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

  const vaultPct =
    data && data.total_bytes > 0
      ? (data.vault_bytes / data.total_bytes) * 100
      : 0;
  const dbPct =
    data && data.total_bytes > 0
      ? (data.database_bytes / data.total_bytes) * 100
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
            <p className="text-xs text-text-muted">Total</p>
            <p className="text-lg font-semibold text-text-primary tabular-nums">
              {formatBytes(data.total_bytes)}
            </p>
          </div>

          {/* Combined usage bar */}
          <div className="h-2 w-full overflow-hidden rounded-full bg-bg-surface mb-3">
            <div
              className="h-full rounded-full bg-accent transition-[width] duration-300"
              style={{ width: `${Math.min(vaultPct + dbPct, 100)}%` }}
            />
          </div>

          <div className="space-y-2">
            {/* Vault row */}
            <div>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs text-text-secondary">Vault</span>
                <span className="text-xs text-text-muted tabular-nums">
                  {formatBytes(data.vault_bytes)}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-surface">
                <div
                  className="h-full rounded-full bg-accent transition-[width] duration-300"
                  style={{ width: `${vaultPct}%` }}
                />
              </div>
            </div>

            {/* Database row */}
            <div>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs text-text-secondary">Database</span>
                <span className="text-xs text-text-muted tabular-nums">
                  {formatBytes(data.database_bytes)}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-surface">
                <div
                  className="h-full rounded-full bg-accent/60 transition-[width] duration-300"
                  style={{ width: `${dbPct}%` }}
                />
              </div>
            </div>
          </div>

          {/* By-type breakdown */}
          {Object.keys(data.by_type ?? {}).length > 0 && (
            <div className="mt-3 border-t border-border-subtle pt-3">
              <p className="mb-1 block text-xs text-text-muted">
                Breakdown by type
              </p>
              <div className="space-y-1">
                {Object.entries(data.by_type).map(([type, bytes]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-xs text-text-secondary capitalize">
                      {type.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-text-muted tabular-nums">
                      {formatBytes(bytes)}
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
