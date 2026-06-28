"use client";

import { useState, useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { environment, type EnvironmentInfo } from "@/features/awareness/api";

// ── Safe variable keys (whitelist for display) ──────────────────────────────

const SAFE_VARS = [
  "HOME",
  "USER",
  "SHELL",
  "TERM",
  "LANG",
  "PATH",
  "NODE_ENV",
  "APP_NAME",
  "API_V1_PREFIX",
  "CORTEX_ROOT",
  "MEMORY_PATH",
  "VAULT_PATH",
];

// ── Skeleton ────────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <Card role="article" aria-label="Environment info loading">
      <div className="space-y-3">
        <Skeleton className="h-4 w-36" />
        <div className="space-y-1.5">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-2 w-3/4" />
          <Skeleton className="h-2 w-1/2" />
        </div>
        <div className="space-y-1.5">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-2 w-5/6" />
        </div>
        <div className="space-y-1.5">
          <Skeleton className="h-3 w-28" />
          <Skeleton className="h-2 w-3/4" />
        </div>
      </div>
    </Card>
  );
}

// ── Component ───────────────────────────────────────────────────────────────

export function EnvironmentCard() {
  const [data, setData] = useState<EnvironmentInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    environment
      .info()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load environment info");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <Card role="article" aria-label="Environment info error">
        <p className="text-xs text-danger">{error}</p>
      </Card>
    );
  }

  if (!data) return <SkeletonCard />;

  // Filter to safe variables only
  const safeVars = Object.entries(data.variables).filter(([key]) =>
    SAFE_VARS.includes(key),
  );

  return (
    <Card role="article" aria-label="Environment info">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-text-primary">Environment</h3>

        {/* Safe Variables */}
        <div className="space-y-1">
          <p className="text-xs font-medium text-text-muted">Variables</p>
          {safeVars.length === 0 ? (
            <p className="text-xs text-text-muted italic">No safe variables available</p>
          ) : (
            <div className="space-y-0.5">
              {safeVars.map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center gap-2 rounded bg-bg-surface px-2 py-1"
                >
                  <span className="font-mono text-[0.625rem] text-accent">{key}</span>
                  <span className="font-mono text-[0.625rem] text-text-secondary truncate">
                    {value}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Paths */}
        <div className="space-y-1">
          <p className="text-xs font-medium text-text-muted">System Paths</p>
          <div className="space-y-0.5">
            {data.paths.slice(0, 6).map((p, i) => (
              <p
                key={i}
                className="font-mono text-[0.625rem] text-text-secondary truncate"
                title={p}
              >
                {p}
              </p>
            ))}
            {data.paths.length > 6 && (
              <p className="text-[0.625rem] text-text-muted italic">
                +{data.paths.length - 6} more
              </p>
            )}
          </div>
        </div>

        {/* Working Directory */}
        <div className="space-y-1">
          <p className="text-xs font-medium text-text-muted">Working Directory</p>
          <p
            className="font-mono text-[0.625rem] text-text-secondary truncate"
            title={data.working_directory}
          >
            {data.working_directory}
          </p>
        </div>
      </div>
    </Card>
  );
}
