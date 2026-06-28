"use client";

import { useState, useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Badge } from "@/shared/ui/Badge";
import { project, type ProjectInfo } from "@/features/awareness/api";

// ── Skeleton ────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <Card role="article" aria-label="Project info loading">
      <div className="animate-pulse space-y-3">
        <div className="h-4 w-32 rounded bg-bg-surface" />
        <div className="h-3 w-44 rounded bg-bg-surface" />
        <div className="h-3 w-36 rounded bg-bg-surface" />
        <div className="flex gap-1.5">
          <div className="h-4 w-14 rounded-full bg-bg-surface" />
          <div className="h-4 w-10 rounded-full bg-bg-surface" />
          <div className="h-4 w-12 rounded-full bg-bg-surface" />
        </div>
        <div className="h-11 w-full rounded-md bg-bg-surface" />
        <div className="h-11 w-32 rounded-md bg-bg-surface" />
      </div>
    </Card>
  );
}

// ── Badge helper ────────────────────────────────────────────────────────────

function ConfigBadge({
  label,
  value,
}: {
  label: string;
  value: boolean | undefined;
}) {
  if (value === undefined) return null;
  return (
    <Badge variant={value ? "success" : "warning"}>{label}</Badge>
  );
}

// ── Component ───────────────────────────────────────────────────────────────

export function ProjectCard() {
  const [data, setData] = useState<ProjectInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [path, setPath] = useState("");

  useEffect(() => {
    let cancelled = false;
    project
      .scan()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load project info");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setError(null);
    try {
      const res = await project.scan();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  if (error && !data) {
    return (
      <Card role="article" aria-label="Project info error">
        <p className="text-xs text-danger">{error}</p>
      </Card>
    );
  }

  if (!data && !error) return <Skeleton />;

  const frameworks = data?.frameworks ?? [];
  const config = data?.config ?? {};

  return (
    <Card role="article" aria-label="Project info">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-text-primary">Project</h3>

        {data ? (
          <>
            {/* Name & Type */}
            <p className="text-xs text-text-secondary">
              <span className="font-medium text-text-muted">Name:</span> {data.name}
            </p>
            <p className="text-xs text-text-secondary">
              <span className="font-medium text-text-muted">Type:</span> {data.type}
            </p>

            {/* Frameworks */}
            {frameworks.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-medium text-text-muted">Frameworks</p>
                <div className="flex flex-wrap gap-1">
                  {frameworks.map((f) => (
                    <Badge key={f} variant="default">
                      {f}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Config Badges */}
            <div className="flex flex-wrap gap-1.5">
              <ConfigBadge label="Tests" value={config.has_tests} />
              <ConfigBadge label="CI" value={config.has_ci} />
              <ConfigBadge label="Docker" value={config.has_docker} />
            </div>
          </>
        ) : (
          <p className="text-xs text-text-muted italic">
            {error || "No project scanned yet"}
          </p>
        )}

        {/* Error display when data exists */}
        {error && data && (
          <p className="text-xs text-danger">{error}</p>
        )}

        {/* Path Input & Scan Button */}
        <Input
          placeholder="/path/to/project"
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
        <Button onClick={handleScan} loading={scanning} size="sm">
          Scan Project
        </Button>
      </div>
    </Card>
  );
}
