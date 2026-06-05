"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Loader } from "../../src/shared/ui";

function formatGb(value) {
  if (value === null || value === undefined) return "n/a";
  return `${Number(value).toFixed(1)} GB`;
}

function formatPercent(value) {
  if (value === null || value === undefined) return "0%";
  return `${Math.round(value)}%`;
}

function formatSize(model) {
  return model?.size_label || model?.size || model?.parameters || "unknown";
}

function ProgressBar({ value = 0, tone = "cyan" }) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  const fill =
    tone === "green" ? "bg-cortex-green" : tone === "warning" ? "bg-cortex-warning" : "bg-cortex-cyan";

  return (
    <div className="h-2 overflow-hidden rounded-cortex-pill border border-cortex-border bg-cortex-bg-secondary/80">
      <div
        className={["h-full rounded-cortex-pill shadow-cortex-cyan transition-[width] duration-cortex", fill].join(" ")}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

function ComponentCard({ model, onDownload, downloading }) {
  const hardware = model?.hardware || {};
  const ram = hardware.ram || {};
  const cpu = hardware.cpu || {};
  const isInstalled = String(model?.download_status || "").toLowerCase() === "installed";
  const percent = model?.download_percent || (isInstalled ? 100 : 0);
  const vram = model?.vram_label || model?.vram_estimate || "N/A";

  return (
    <Card className="flex flex-col gap-cortex-16">
      <div className="flex items-start justify-between gap-cortex-12">
        <div className="min-w-0">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Model Module</p>
          <h2 className="mt-cortex-8 truncate text-lg font-medium text-cortex-text">{model.name}</h2>
          <p className="mt-cortex-4 font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
            {model.provider_name || "local"}
          </p>
        </div>
        <Badge variant={isInstalled ? "green" : "warning"}>
          {isInstalled ? "installed" : model.download_status || "available"}
        </Badge>
      </div>

      <div className="grid gap-cortex-8 md:grid-cols-2">
        <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
            VRAM / size
          </div>
          <div className="mt-cortex-8 font-mono text-sm text-cortex-text">
            {vram} · {formatSize(model)}
          </div>
        </div>
        <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
            Context window
          </div>
          <div className="mt-cortex-8 font-mono text-sm text-cortex-text">
            {model.context_window || model.context_length || "n/a"}
          </div>
        </div>
      </div>

      <div className="grid gap-cortex-8 md:grid-cols-3">
        <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">CPU</div>
          <div className="mt-cortex-8 font-mono text-sm text-cortex-text">{cpu.usage_percent || 0}%</div>
        </div>
        <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">RAM</div>
          <div className="mt-cortex-8 font-mono text-sm text-cortex-text">{formatPercent(ram.usage_percent)}</div>
        </div>
        <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
            State
          </div>
          <div className="mt-cortex-8 font-mono text-sm text-cortex-text">
            {model.status || "active"}
          </div>
        </div>
      </div>

      <div className="grid gap-cortex-8">
        <div className="flex items-center justify-between gap-cortex-12 font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
          <span>Download progress</span>
          <span>{formatPercent(percent)}</span>
        </div>
        <ProgressBar value={percent} tone={isInstalled ? "green" : "cyan"} />
      </div>

      <div className="flex items-center justify-between gap-cortex-12">
        <div className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
          {downloading ? "queued / downloading" : "registry component"}
        </div>
        {!isInstalled ? (
          <Button variant="primary" size="sm" onClick={() => onDownload(model.name)} disabled={downloading}>
            Download
          </Button>
        ) : (
          <Badge variant="green">ready</Badge>
        )}
      </div>
    </Card>
  );
}

function Toggle({ label, value, onChange, helper }) {
  return (
    <label className="flex items-start justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
      <div>
        <div className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">{label}</div>
        {helper ? <div className="mt-cortex-4 text-sm text-cortex-text-muted">{helper}</div> : null}
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={[
          "relative h-6 w-11 rounded-cortex-pill border transition duration-cortex",
          value
            ? "border-cortex-cyan/30 bg-cortex-cyan/10 shadow-cortex-cyan"
            : "border-cortex-border bg-transparent",
        ].join(" ")}
      >
        <span
          className={[
            "absolute top-0.5 h-5 w-5 rounded-full transition duration-cortex",
            value ? "left-5 bg-cortex-cyan" : "left-0.5 bg-cortex-text-muted",
          ].join(" ")}
        />
      </button>
    </label>
  );
}

export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [downloads, setDownloads] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function loadData() {
    try {
      const [localRes, downloadsRes, configRes] = await Promise.all([
        fetch("/api/models/local", { cache: "no-store" }),
        fetch("/api/models/downloads", { cache: "no-store" }),
        fetch("/api/models/config", { cache: "no-store" }),
      ]);

      const localData = await localRes.json();
      const downloadData = await downloadsRes.json();
      const configData = await configRes.json();

      if (!localRes.ok) throw new Error(localData?.error || "Failed to load local models");
      if (!downloadsRes.ok) throw new Error(downloadData?.error || "Failed to load downloads");
      if (!configRes.ok) throw new Error(configData?.error || "Failed to load config");

      setModels(Array.isArray(localData) ? localData : []);
      setDownloads(Array.isArray(downloadData) ? downloadData : []);
      setConfig(configData || {});
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to load models");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const timer = window.setInterval(loadData, 8000);
    return () => window.clearInterval(timer);
  }, []);

  async function downloadModel(modelName) {
    setError("");
    try {
      const response = await fetch("/api/models/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: modelName }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.error || "Download request failed");
      await loadData();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Download request failed");
    }
  }

  async function saveConfig(nextConfig) {
    setSaving(true);
    setError("");
    try {
      const response = await fetch("/api/models/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nextConfig),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.error || "Config update failed");
      setConfig(data);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Config update failed");
    } finally {
      setSaving(false);
    }
  }

  const activeDownloads = useMemo(
    () => downloads.filter((job) => !["completed", "cancelled", "failed"].includes(String(job.status || "").toLowerCase())),
    [downloads]
  );
  const primaryHardware = models.find((model) => model.hardware) || null;
  const hw = primaryHardware?.hardware || {};

  return (
    <section className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.4fr)_360px]">
      <div className="grid gap-cortex-16">
        <div className="flex items-start justify-between gap-cortex-16">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Model Management</p>
            <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">GPU Control Panel</h1>
            <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
              Technical registry view for local models, download jobs, and boot-time configuration.
            </p>
          </div>
          <div className="flex items-center gap-cortex-12">
            <Badge variant="neutral">{models.length} modules</Badge>
            <Button variant="secondary" size="sm" onClick={loadData}>
              Refresh
            </Button>
          </div>
        </div>

        {error ? (
          <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
            <div className="font-mono text-sm">Error: {error}</div>
          </Card>
        ) : null}

        <div className="grid gap-cortex-16 md:grid-cols-2">
          <Card>
            <div className="flex items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Hardware</p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Control substrate</h2>
              </div>
              <Badge variant="cyan">live</Badge>
            </div>
            <div className="mt-cortex-16 grid gap-cortex-8">
              <div className="flex items-center justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">CPU</span>
                <span className="font-mono text-sm text-cortex-text">{hw.cpu?.usage_percent || 0}%</span>
              </div>
              <div className="flex items-center justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">RAM</span>
                <span className="font-mono text-sm text-cortex-text">{formatPercent(hw.ram?.usage_percent)}</span>
              </div>
              <div className="flex items-center justify-between gap-cortex-12 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">GPU</span>
                <span className="font-mono text-sm text-cortex-text">
                  {hw.gpu?.detected ? `${hw.gpu.name} · ${formatPercent(hw.gpu.utilization)}` : "not detected"}
                </span>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between gap-cortex-12">
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Status</p>
                <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Registry overview</h2>
              </div>
              <Badge variant={activeDownloads.length ? "warning" : "green"}>
                {activeDownloads.length ? "busy" : "stable"}
              </Badge>
            </div>
            <div className="mt-cortex-16 grid gap-cortex-8">
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                  Selected model
                </div>
                <div className="mt-cortex-8 font-mono text-sm text-cortex-text">
                  {config?.selected_model || config?.preferred_model || "Auto"}
                </div>
              </div>
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                  Routing profile
                </div>
                <div className="mt-cortex-8 font-mono text-sm text-cortex-text">
                  {config?.active_profile || "Balanced"}
                </div>
              </div>
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                  Updated
                </div>
                <div className="mt-cortex-8 font-mono text-sm text-cortex-text">live</div>
              </div>
            </div>
          </Card>
        </div>

        <Card className="flex flex-col gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Local Models</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Hardware-like registry cards</h2>
            </div>
            {loading ? <Loader /> : <Badge variant="neutral">{models.length} loaded</Badge>}
          </div>

          <div className="grid gap-cortex-16 xl:grid-cols-2">
            {models.map((model) => (
              <ComponentCard
                key={model.id || model.name}
                model={model}
                onDownload={downloadModel}
                downloading={Boolean(model.download_status && model.download_status !== "installed")}
              />
            ))}
          </div>
        </Card>

        <Card className="flex flex-col gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                Download jobs
              </p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Terminal progress bars</h2>
            </div>
            <Badge variant="neutral">{downloads.length} jobs</Badge>
          </div>

          <div className="grid gap-cortex-8">
            {downloads.length > 0 ? (
              downloads.map((job) => {
                const tone =
                  job.status === "completed" ? "green" : job.status === "failed" ? "warning" : "cyan";
                return (
                  <div
                    key={job.id}
                    className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12"
                  >
                    <div className="flex items-center justify-between gap-cortex-12">
                      <div>
                        <div className="font-mono text-sm text-cortex-text">{job.model}</div>
                        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                          {job.status} · {job.message || "queued"}
                        </div>
                      </div>
                      <Badge variant={tone}>{job.percent || 0}%</Badge>
                    </div>
                    <ProgressBar value={job.percent || 0} tone={tone} />
                  </div>
                );
              })
            ) : (
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                No active download jobs.
              </div>
            )}
          </div>
        </Card>
      </div>

      <aside className="grid gap-cortex-16">
        <Card className="flex flex-col gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">BIOS</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Configuration panel</h2>
            </div>
            <Badge variant="cyan">editable</Badge>
          </div>

          {config ? (
            <div className="grid gap-cortex-8">
              <Toggle
                label="Local only"
                value={Boolean(config.local_only)}
                onChange={(value) => setConfig((current) => ({ ...current, local_only: value }))}
                helper="Prefer installed local models."
              />
              <Toggle
                label="Auto download"
                value={Boolean(config.auto_download)}
                onChange={(value) => setConfig((current) => ({ ...current, auto_download: value }))}
                helper="Queue missing modules automatically."
              />
              <Toggle
                label="GPU acceleration"
                value={Boolean(config.gpu_acceleration)}
                onChange={(value) => setConfig((current) => ({ ...current, gpu_acceleration: value }))}
                helper="Enable GPU-aware routing."
              />
              <label className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                  Preferred model
                </span>
                <input
                  value={config.preferred_model || ""}
                  onChange={(event) =>
                    setConfig((current) => ({ ...current, preferred_model: event.target.value }))
                  }
                  className="w-full rounded-cortex border border-cortex-border bg-transparent px-cortex-12 py-cortex-12 font-mono text-sm text-cortex-text outline-none transition duration-cortex focus:border-cortex-cyan/35 focus:shadow-cortex-cyan"
                />
              </label>
              <label className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                  Context strategy
                </span>
                <select
                  value={config.context_strategy || "balanced"}
                  onChange={(event) =>
                    setConfig((current) => ({ ...current, context_strategy: event.target.value }))
                  }
                  className="w-full rounded-cortex border border-cortex-border bg-transparent px-cortex-12 py-cortex-12 font-mono text-sm text-cortex-text outline-none transition duration-cortex focus:border-cortex-cyan/35 focus:shadow-cortex-cyan"
                >
                  <option value="balanced">balanced</option>
                  <option value="local-first">local-first</option>
                  <option value="quality-first">quality-first</option>
                  <option value="gpu-max">gpu-max</option>
                </select>
              </label>
              <div className="flex items-center justify-between gap-cortex-12 pt-cortex-8">
                <Badge variant="neutral">selected: {config.selected_model || "Auto"}</Badge>
                <Button variant="primary" size="sm" onClick={() => saveConfig(config)} disabled={saving}>
                  {saving ? "Writing..." : "Save BIOS"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
              Loading configuration...
            </div>
          )}
        </Card>

        <Card className="flex flex-col gap-cortex-12">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                Download terminal
              </p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Status console</h2>
            </div>
            <Badge variant="neutral">live</Badge>
          </div>
          <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
            <div className="mb-cortex-8">Active queue: {activeDownloads.length}</div>
            <div>{activeDownloads.length ? "Streaming progress bars are active." : "No download activity."}</div>
          </div>
        </Card>
      </aside>
    </section>
  );
}
