"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { indexingApi } from "@/shared/api/indexing";
import type { IndexingConfig, IndexingPreview, IndexingStatus } from "@/shared/types";
import Card from "@/shared/ui/Card";
import Input from "@/shared/ui/Input";
import Button from "@/shared/ui/Button";

export default function IndexingConfigForm() {
  const [config, setConfig] = useState<IndexingConfig | null>(null);
  const [defaults, setDefaults] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [previewPath, setPreviewPath] = useState("");
  const [preview, setPreview] = useState<IndexingPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [status, setStatus] = useState<IndexingStatus | null>(null);

  const [includePaths, setIncludePaths] = useState("");
  const [excludePaths, setExcludePaths] = useState("");
  const [includePatterns, setIncludePatterns] = useState("");
  const [excludePatterns, setExcludePatterns] = useState("");
  const [maxFileSize, setMaxFileSize] = useState(1_000_000);
  const [followSymlinks, setFollowSymlinks] = useState(false);
  const [syncEnabled, setSyncEnabled] = useState(true);
  const [syncInterval, setSyncInterval] = useState(300);
  const [priority, setPriority] = useState(0);

  useEffect(() => {
    indexingApi.get().then((res) => {
      if (res.config) {
        setConfig(res.config);
        setDefaults(false);
        setIncludePaths((res.config.include_paths || []).join(", "));
        setExcludePaths((res.config.exclude_paths || []).join(", "));
        setIncludePatterns((res.config.include_patterns || []).join(", "));
        setExcludePatterns((res.config.exclude_patterns || []).join(", "));
        setMaxFileSize(res.config.max_file_size_bytes);
        setFollowSymlinks(res.config.follow_symlinks);
        setSyncEnabled(res.config.sync_enabled);
        setSyncInterval(res.config.sync_interval_seconds);
        setPriority(res.config.priority);
      }
      setLoading(false);
    });
    indexingApi.status().then((res) => {
      setStatus(res);
    }).catch(() => {
      // silent
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      await indexingApi.update({
        name: "default",
        include_paths: includePaths.split(",").map((s) => s.trim()).filter(Boolean),
        exclude_paths: excludePaths.split(",").map((s) => s.trim()).filter(Boolean),
        include_patterns: includePatterns.split(",").map((s) => s.trim()).filter(Boolean),
        exclude_patterns: excludePatterns.split(",").map((s) => s.trim()).filter(Boolean),
        max_file_size_bytes: maxFileSize,
        follow_symlinks: followSymlinks,
        sync_enabled: syncEnabled,
        sync_interval_seconds: syncInterval,
        priority,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // silent
    } finally {
      setSaving(false);
    }
  }

  async function handlePreview() {
    if (!previewPath.trim()) return;
    setPreviewLoading(true);
    try {
      const result = await indexingApi.preview(previewPath.trim());
      setPreview(result);
    } catch {
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  }

  const fadeUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { type: "spring" as const, damping: 25, stiffness: 200 },
  };

  if (loading) return null;

  return (
    <motion.div {...fadeUp}>
      <Card gradient className="p-5 mb-5">
        <h2 className="text-sm font-medium text-text mb-3">Indexing Status</h2>
        {status ? (
          <div className="grid grid-cols-4 gap-3 mb-3">
            {[
              { label: "Watching", value: status.watching },
              { label: "Indexed Files", value: status.indexed_files },
              { label: "Pending Changes", value: status.pending_changes },
              { label: "Errors", value: status.errors },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-bg-surface p-2 border border-border-subtle text-center">
                <div className="text-sm font-semibold text-text">{stat.value}</div>
                <div className="text-[10px] text-text-muted mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-muted">Loading status...</p>
        )}
        {status && status.watched_paths.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-text-secondary mb-1">Watched Paths:</p>
            <div className="flex flex-wrap gap-1">
              {status.watched_paths.map((p) => (
                <span key={p} className="text-[10px] bg-bg-surface border border-border-subtle rounded px-1.5 py-0.5 text-text-muted">{p}</span>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card gradient className="p-5">
        <h2 className="text-sm font-medium text-text mb-4">Indexing Configuration</h2>
        <p className="text-xs text-text-muted mb-4">
          Control which files are included or excluded during indexing.
          {defaults && <span className="text-accent ml-1">Using defaults.</span>}
        </p>

        <div className="grid gap-4">
          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Include Paths</label>
            <Input
              placeholder="src/, lib/, (comma-separated)"
              value={includePaths}
              onChange={(e) => setIncludePaths(e.target.value)}
            />
          </div>

          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Exclude Paths</label>
            <Input
              placeholder="node_modules/, dist/, (comma-separated)"
              value={excludePaths}
              onChange={(e) => setExcludePaths(e.target.value)}
            />
          </div>

          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Include Patterns</label>
            <Input
              placeholder="*.ts, *.py, (comma-separated)"
              value={includePatterns}
              onChange={(e) => setIncludePatterns(e.target.value)}
            />
          </div>

          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Exclude Patterns</label>
            <Input
              placeholder="*.test.*, *.min.*, (comma-separated)"
              value={excludePatterns}
              onChange={(e) => setExcludePatterns(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Max File Size (bytes)</label>
              <Input
                type="number"
                value={String(maxFileSize)}
                onChange={(e) => setMaxFileSize(Number(e.target.value))}
              />
            </div>
            <div className="grid gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Sync Interval (seconds)</label>
              <Input
                type="number"
                value={String(syncInterval)}
                onChange={(e) => setSyncInterval(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Priority</label>
              <Input
                type="number"
                value={String(priority)}
                onChange={(e) => setPriority(Number(e.target.value))}
              />
            </div>
            <div />
          </div>

          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={followSymlinks}
                onChange={(e) => setFollowSymlinks(e.target.checked)}
                className="rounded border-border-subtle bg-bg-surface text-accent focus:ring-accent/20"
              />
              <span className="text-xs text-text-secondary">Follow Symlinks</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={syncEnabled}
                onChange={(e) => setSyncEnabled(e.target.checked)}
                className="rounded border-border-subtle bg-bg-surface text-accent focus:ring-accent/20"
              />
              <span className="text-xs text-text-secondary">Sync Enabled</span>
            </label>
          </div>

          {saved && <p className="text-sm text-success bg-success/10 rounded-xl px-3 py-2 border border-success/10">Configuration saved.</p>}

          <div className="flex justify-end">
            <Button size="sm" loading={saving} onClick={handleSave}>Save configuration</Button>
          </div>
        </div>

        <hr className="my-5 border-border-subtle" />

        <h3 className="text-sm font-medium text-text mb-3">Preview Indexing</h3>
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder="/path/to/repo"
              value={previewPath}
              onChange={(e) => setPreviewPath(e.target.value)}
            />
          </div>
          <Button size="sm" loading={previewLoading} onClick={handlePreview}>Preview</Button>
        </div>

        {preview && (
          <div className="mt-4 grid grid-cols-5 gap-3 text-center">
            {[
              { label: "Total Files", value: preview.total_files },
              { label: "Will Index", value: preview.will_index },
              { label: "Excl. by Dir", value: preview.excluded_by_directory },
              { label: "Excl. by Pattern", value: preview.excluded_by_pattern },
              { label: "Excl. by Size", value: preview.excluded_by_size },
            ].map((stat) => (
              <div key={stat.label} className="rounded-lg bg-bg-surface p-2 border border-border-subtle">
                <div className="text-sm font-semibold text-text">{stat.value}</div>
                <div className="text-[10px] text-text-muted mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </motion.div>
  );
}
