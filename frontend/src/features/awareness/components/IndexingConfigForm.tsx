"use client";

import { useState, useEffect } from "react";
import { indexing, type IndexingConfig } from "../api";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";

function ConfigSkeleton() {
  return (
    <Card className="p-6 space-y-5">
      <Skeleton className="h-5 w-44" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-20 w-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-20 w-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-10 w-48" />
      </div>
      <Skeleton className="h-5 w-28" />
      <Skeleton className="h-11 w-44" />
    </Card>
  );
}

export function IndexingConfigForm() {
  const [config, setConfig] = useState<IndexingConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [previewDir, setPreviewDir] = useState("");
  const [previewResult, setPreviewResult] = useState<{
    files: string[];
    total: number;
    estimated_time: number;
  } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const loadConfig = () => {
    setLoading(true);
    setFetchError(null);
    indexing
      .config()
      .then(setConfig)
      .catch((e) =>
        setFetchError(e instanceof Error ? e.message : "Failed to load config"),
      )
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await indexing.saveConfig(config);
      setSaveSuccess(true);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Failed to save config");
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    if (!previewDir.trim()) return;
    setPreviewLoading(true);
    setPreviewResult(null);
    setSaveError(null);
    try {
      const result = await indexing.preview({ directory: previewDir });
      setPreviewResult(result);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setPreviewLoading(false);
    }
  };

  if (loading) return <ConfigSkeleton />;

  if (fetchError) {
    return (
      <Card className="p-6">
        <p className="text-sm text-red-400">{fetchError}</p>
        <Button className="mt-3" variant="ghost" onClick={loadConfig}>
          Retry
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Configuration Section */}
      <Card className="p-6 space-y-5">
        <h2 className="text-base font-semibold text-text-primary">
          Indexing Settings
        </h2>

        {/* Watched Directories */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            Watched Directories
          </label>
          <textarea
            className="w-full h-20 rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-secondary font-mono focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none resize-none"
            value={config?.watched_directories?.join("\n") ?? ""}
            onChange={(e) =>
              setConfig({
                ...config!,
                watched_directories: e.target.value
                  .split("\n")
                  .filter(Boolean),
              })
            }
            placeholder="One path per line"
          />
        </div>

        {/* Ignore Patterns */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            Ignore Patterns
          </label>
          <textarea
            className="w-full h-20 rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-secondary font-mono focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none resize-none"
            value={config?.ignore_patterns?.join("\n") ?? ""}
            onChange={(e) =>
              setConfig({
                ...config!,
                ignore_patterns: e.target.value
                  .split("\n")
                  .filter(Boolean),
              })
            }
            placeholder="One pattern per line (glob syntax)"
          />
        </div>

        {/* Max File Size */}
        <div>
          <Input
            label="Max File Size (bytes)"
            type="number"
            min={0}
            className="w-full max-w-xs"
            value={config?.max_file_size ?? 0}
            onChange={(e) =>
              setConfig({
                ...config!,
                max_file_size: parseInt(e.target.value) || 0,
              })
            }
          />
        </div>

        {/* Sync Enabled */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={config?.enabled ?? false}
            onChange={(e) =>
              setConfig({ ...config!, enabled: e.target.checked })
            }
            className="rounded border-border-default bg-bg-surface text-accent focus:ring-accent/50 focus:ring-2 focus:outline-none"
          />
          <span className="text-sm text-text-primary">Sync Enabled</span>
        </label>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-1">
          <Button onClick={handleSave} disabled={saving} variant="primary">
            {saving ? "Saving..." : "Save Configuration"}
          </Button>
          {saveSuccess && (
            <span className="text-sm text-green-400">
              Configuration saved
            </span>
          )}
          {saveError && (
            <span className="text-sm text-red-400">{saveError}</span>
          )}
        </div>
      </Card>

      {/* Preview Section */}
      <Card className="p-6 space-y-4">
        <h2 className="text-base font-semibold text-text-primary">
          Preview Indexing
        </h2>
        <p className="text-sm text-text-secondary">
          Preview what files would be indexed in a given directory
        </p>
        <div className="flex gap-3">
          <input
            className="flex-1 h-11 rounded-md border border-border-default bg-bg-surface px-3 text-sm text-text-primary placeholder:text-text-muted focus:border-border-accent focus:shadow-[0_0_0_2px_rgba(14,165,201,0.12)] focus:outline-none"
            type="text"
            placeholder="/path/to/directory"
            value={previewDir}
            onChange={(e) => setPreviewDir(e.target.value)}
          />
          <Button
            onClick={handlePreview}
            disabled={previewLoading || !previewDir.trim()}
            variant="primary"
          >
            {previewLoading ? "Scanning..." : "Preview"}
          </Button>
        </div>
        {previewResult && (
          <div className="space-y-2">
            <p className="text-sm text-text-secondary">
              Found{" "}
              <span className="font-semibold text-text-primary">
                {previewResult.total}
              </span>{" "}
              files -- estimated{" "}
              <span className="font-semibold text-text-primary">
                {previewResult.estimated_time}s
              </span>
            </p>
            {previewResult.files.length > 0 ? (
              <ul className="max-h-48 overflow-y-auto border border-border-default rounded-md bg-bg-surface p-2 space-y-0.5">
                {previewResult.files.map((f, i) => (
                  <li
                    key={i}
                    className="text-xs text-text-secondary font-mono truncate"
                    title={f}
                  >
                    {f}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                title="No files found"
                description="The directory does not contain indexable files."
              />
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
