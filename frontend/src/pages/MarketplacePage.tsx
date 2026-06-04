import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/appStore";
import {
  getMarketplace,
  getHardwareInfo,
  listModelDownloads,
  startModelDownload,
  cancelModelDownload,
  resumeModelDownload,
  type MarketplaceModel,
  type ModelDownloadJob,
} from "@/api/ai";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Download,
  Loader2,
  Pause,
  Search,
  Sparkles,
  Wand2,
} from "lucide-react";

type FilterKey = "all" | "coding" | "chat" | "reasoning" | "cloud" | "installed" | "fast";

function formatGb(value?: number | null) {
  if (value == null || Number.isNaN(value)) return "N/A";
  return `${value.toFixed(1)} GB`;
}

function formatEta(download?: ModelDownloadJob) {
  if (!download?.total || !download?.completed || download.completed <= 0 || download.completed >= download.total) {
    return "ETA unavailable";
  }

  const elapsedSeconds = Math.max((Date.now() - new Date(download.created_at).getTime()) / 1000, 1);
  const bytesPerSecond = download.completed / elapsedSeconds;
  if (!Number.isFinite(bytesPerSecond) || bytesPerSecond <= 0) return "ETA unavailable";

  const remainingSeconds = (download.total - download.completed) / bytesPerSecond;
  if (!Number.isFinite(remainingSeconds) || remainingSeconds < 0) return "ETA unavailable";

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = Math.max(Math.round(remainingSeconds % 60), 0);
  if (minutes > 0) {
    return `ETA ${minutes}m ${seconds}s`;
  }
  return `ETA ${seconds}s`;
}

export function MarketplacePage() {
  const qc = useQueryClient();
  const setToast = useAppStore((s) => s.setToast);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");

  const { data: hardware, isLoading: loadingHardware } = useQuery({
    queryKey: ["hardwareInfo"],
    queryFn: getHardwareInfo,
    refetchInterval: 15000,
  });

  const { data: downloadJobs = [] } = useQuery({
    queryKey: ["modelDownloads"],
    queryFn: listModelDownloads,
    refetchInterval: 2000,
  });

  const { data: catalog = [], isLoading: loadingCatalog } = useQuery<MarketplaceModel[]>({
    queryKey: ["marketplace", searchQuery],
    queryFn: () => getMarketplace(searchQuery.trim() || undefined),
  });

  const recommendations = useMemo(() => {
    if (!hardware) return [];

    const vram = hardware.gpu.detected ? hardware.gpu.total_vram_gb : 0;
    const ram = hardware.ram.total_gb;
    return catalog
      .filter((model) => !model.is_installed)
      .filter((model) => {
        if (vram > 0) return model.vram_requirement_gb <= Math.max(2, vram - 0.5);
        return model.vram_requirement_gb <= Math.min(8, Math.max(4, ram / 4));
      })
      .slice(0, 3);
  }, [catalog, hardware]);

  const filteredCatalog = useMemo(() => {
    return catalog.filter((model) => {
      if (activeFilter === "installed") return model.is_installed;
      if (activeFilter === "coding") return model.tags.some((tag) => tag.toLowerCase() === "coding");
      if (activeFilter === "chat") return model.tags.some((tag) => tag.toLowerCase() === "chat");
      if (activeFilter === "reasoning") return model.tags.some((tag) => tag.toLowerCase() === "reasoning");
      if (activeFilter === "cloud") return model.source?.toLowerCase().includes("cloud") || model.tags.some((tag) => tag.toLowerCase() === "cloud");
      if (activeFilter === "fast") return model.performance_tier === "fast" || model.vram_requirement_gb <= 6;
      return true;
    });
  }, [activeFilter, catalog]);

  const handleDownload = async (modelName: string) => {
    try {
      const job = await startModelDownload(modelName);
      setToast(`${job.status}: ${job.model}`);
      qc.invalidateQueries({ queryKey: ["marketplace"] });
      qc.invalidateQueries({ queryKey: ["models"] });
      qc.invalidateQueries({ queryKey: ["modelDownloads"] });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed";
      setToast(`Failed to download ${modelName}: ${message}`);
    }
  };

  const cancelDownload = async (modelName: string) => {
    const activeJob = downloadJobs.find((job) => job.model === modelName && !["completed", "failed", "cancelled"].includes(job.status));
    if (!activeJob) return;
    await cancelModelDownload(activeJob.id);
    qc.invalidateQueries({ queryKey: ["modelDownloads"] });
    setToast(`Cancelled ${modelName}`);
  };

  const resumeDownload = async (modelName: string) => {
    const resumable = downloadJobs.find((job) => job.model === modelName && ["cancelled", "failed"].includes(job.status));
    if (!resumable) return;
    await resumeModelDownload(resumable.id);
    qc.invalidateQueries({ queryKey: ["modelDownloads"] });
    setToast(`Resumed ${modelName}`);
  };

  const marketStats = [
    { label: "Available", value: String(catalog.length), icon: Sparkles },
    { label: "Installed", value: String(catalog.filter((m) => m.is_installed).length), icon: CheckCircle2 },
    { label: "Filtered", value: String(filteredCatalog.length), icon: Wand2 },
    { label: "Recommended", value: String(recommendations.length), icon: Cpu },
  ];

  return (
    <div className="h-full overflow-y-auto bg-cortex-background px-4 py-6 md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-3xl border border-cortex-border bg-gradient-to-br from-cortex-surface/80 via-cortex-surface/50 to-cortex-elevated/20 p-6 shadow-2xl shadow-black/20">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-cortex-accent/20 bg-cortex-accent-soft/50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cortex-accent">
                <Sparkles className="h-3.5 w-3.5" />
                Ollama registry
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight text-cortex-text md:text-4xl">Model Marketplace</h1>
                <p className="mt-2 max-w-3xl text-sm text-cortex-muted">
                  Browse the live Ollama registry, inspect model capabilities, and pull models locally with progress, ETA, and cancellation.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/60 px-4 py-3 text-sm text-cortex-text">
                <p className="text-[11px] uppercase tracking-wider text-cortex-muted">Query</p>
                <p className="mt-1 font-semibold">{searchQuery || "all models"}</p>
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {marketStats.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.label} className="rounded-2xl border border-cortex-border bg-cortex-elevated/60 p-4 transition hover:border-cortex-accent/40 hover:bg-cortex-elevated/80">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">
                    <Icon className="h-4 w-4 text-cortex-accent" />
                    {card.label}
                  </div>
                  <div className="mt-2 text-2xl font-black text-cortex-text">{card.value}</div>
                </div>
              );
            })}
          </div>
        </div>

        <Card className="border-cortex-border bg-cortex-surface/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Cpu className="h-4 w-4 text-cortex-accent" />
              Hardware profile
            </CardTitle>
            <CardDescription>Live compute detection helps surface better local model choices.</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingHardware ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-cortex-accent" />
              </div>
            ) : hardware ? (
              <div className="grid gap-4 lg:grid-cols-4">
                <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                  <p className="text-[11px] uppercase tracking-wider text-cortex-muted">OS</p>
                  <p className="mt-2 font-semibold text-cortex-text">{hardware.os}</p>
                </div>
                <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                  <p className="text-[11px] uppercase tracking-wider text-cortex-muted">CPU</p>
                  <p className="mt-2 truncate font-semibold text-cortex-text" title={hardware.cpu}>{hardware.cpu}</p>
                </div>
                <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                  <p className="text-[11px] uppercase tracking-wider text-cortex-muted">RAM</p>
                  <p className="mt-2 font-semibold text-cortex-text">{hardware.ram.total_gb} GB</p>
                  <div className="mt-3 h-2 rounded-full bg-cortex-border">
                    <div className="h-full rounded-full bg-cortex-accent" style={{ width: `${hardware.ram.usage_percent}%` }} />
                  </div>
                </div>
                <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                  <p className="text-[11px] uppercase tracking-wider text-cortex-muted">GPU</p>
                  {hardware.gpu.detected ? (
                    <>
                      <p className="mt-2 truncate font-semibold text-cortex-success" title={hardware.gpu.name}>{hardware.gpu.name}</p>
                      <p className="mt-1 text-xs text-cortex-muted">VRAM {hardware.gpu.total_vram_gb} GB</p>
                    </>
                  ) : (
                    <>
                      <p className="mt-2 font-semibold text-cortex-warn">CPU only</p>
                      <p className="mt-1 text-xs text-cortex-muted">No compatible GPU detected</p>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-4 text-sm text-cortex-muted">Hardware detection unavailable.</div>
            )}
          </CardContent>
        </Card>

        {recommendations.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-cortex-accent" />
              <h2 className="text-xl font-semibold text-cortex-text">Hardware matched recommendations</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {recommendations.map((model) => (
                <Card key={`rec-${model.name}`} className="border-cortex-accent/30 bg-cortex-surface/50">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="accent">Recommended</Badge>
                      <span className="text-xs text-cortex-muted">{model.size}</span>
                    </div>
                    <CardTitle className="mt-2 text-base">{model.display_name}</CardTitle>
                    <CardDescription className="line-clamp-2 text-xs">{model.best_use_case}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-2 text-xs text-cortex-muted">
                      <div>
                        <p className="uppercase tracking-wider">Context</p>
                        <p className="mt-1 font-semibold text-cortex-text">{model.context_length.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="uppercase tracking-wider">VRAM</p>
                        <p className="mt-1 font-semibold text-cortex-text">{formatGb(model.vram_requirement_gb)}</p>
                      </div>
                    </div>
                    <Button
                      className="w-full gap-2"
                      onClick={() => handleDownload(model.name)}
                      disabled={model.is_installed || downloadJobs.some((job) => job.model === model.name && ["queued", "running"].includes(job.status))}
                    >
                      <Download className="h-4 w-4" />
                      {model.is_installed ? "Installed" : "Quick install"}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-1.5 rounded-2xl border border-cortex-border bg-cortex-elevated/60 p-1">
            {[
              { id: "all", label: "All" },
              { id: "coding", label: "Coding" },
              { id: "chat", label: "Chat" },
              { id: "reasoning", label: "Reasoning" },
              { id: "cloud", label: "Cloud" },
              { id: "fast", label: "Fast" },
              { id: "installed", label: "Installed" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveFilter(tab.id as FilterKey)}
                className={cn(
                  "rounded-xl px-3 py-1.5 text-xs font-semibold transition",
                  activeFilter === tab.id
                    ? "bg-cortex-accent text-cortex-bg shadow-lg shadow-cortex-accent/20"
                    : "text-cortex-muted hover:text-cortex-text",
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative w-full lg:max-w-lg">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-cortex-muted" />
            <Input
              placeholder="Search by model name or capability..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {loadingCatalog ? (
          <div className="flex items-center justify-center rounded-3xl border border-dashed border-cortex-border py-20">
            <Loader2 className="h-8 w-8 animate-spin text-cortex-accent" />
          </div>
        ) : filteredCatalog.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredCatalog.map((model) => {
              const downloadProgress = downloadJobs.find((job) => job.model === model.name && !["completed", "failed", "cancelled"].includes(job.status))
                || downloadJobs.find((job) => job.model === model.name);
              const showWarning = !hardware?.gpu.detected && model.vram_requirement_gb >= 6;
              const isVramTooLow = hardware?.gpu.detected && model.vram_requirement_gb > hardware.gpu.total_vram_gb;
              const warningText = isVramTooLow
                ? `Exceeds detected VRAM (${hardware?.gpu.total_vram_gb} GB).`
                : showWarning
                  ? "CPU only mode will be slow for this model."
                  : null;

              return (
                <Card
                  key={model.name}
                  className={cn(
                    "overflow-hidden border-cortex-border bg-cortex-surface/50 transition hover:border-cortex-accent/40 hover:bg-cortex-surface/70",
                    model.is_installed && "border-cortex-success/40",
                  )}
                >
                  <CardHeader className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex flex-wrap gap-1">
                        {model.tags.map((tag) => (
                          <Badge key={tag} variant="default" className="bg-cortex-elevated text-cortex-muted">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <Badge variant={model.is_installed ? "accent" : "default"}>
                        {model.is_installed ? "Installed" : model.performance_tier || "available"}
                      </Badge>
                    </div>

                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <CardTitle className="truncate text-base">{model.display_name}</CardTitle>
                        <CardDescription className="mt-1 line-clamp-2 text-xs">{model.best_use_case}</CardDescription>
                      </div>
                      <span className="shrink-0 text-xs text-cortex-muted">{model.size}</span>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-3 text-xs text-cortex-muted">
                      <div>
                        <p className="uppercase tracking-wider">Context</p>
                        <p className="mt-1 font-semibold text-cortex-text">{model.context_length.toLocaleString()} tokens</p>
                      </div>
                      <div>
                        <p className="uppercase tracking-wider">VRAM</p>
                        <p className="mt-1 font-semibold text-cortex-text">{formatGb(model.vram_requirement_gb)}</p>
                      </div>
                      <div>
                        <p className="uppercase tracking-wider">Pull</p>
                        <p className="mt-1 truncate font-mono text-[11px] text-cortex-text">{model.pull_command || `ollama pull ${model.name}`}</p>
                      </div>
                      <div>
                        <p className="uppercase tracking-wider">Source</p>
                        <p className="mt-1 font-semibold text-cortex-text">{model.source || "Ollama Registry"}</p>
                      </div>
                    </div>

                    {warningText && (
                      <div className="flex gap-2 rounded-2xl border border-cortex-warn/30 bg-cortex-warn/10 p-3 text-xs text-cortex-warn">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                        <span>{warningText}</span>
                      </div>
                    )}

                    {downloadProgress ? (
                      <div className="space-y-2 rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-3">
                        <div className="flex items-center justify-between text-xs font-semibold">
                          <span className="truncate text-cortex-text">{downloadProgress.status}</span>
                          <span className="text-cortex-accent">{downloadProgress.percent}%</span>
                        </div>
                        <div className="h-2 rounded-full bg-cortex-border">
                          <div
                            className="h-full rounded-full bg-cortex-accent transition-all duration-300"
                            style={{ width: `${downloadProgress.percent}%` }}
                          />
                        </div>
                        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-cortex-muted">
                          <span>
                            {downloadProgress.completed !== undefined && downloadProgress.total ? (
                              <>
                                {(downloadProgress.completed / 1024 / 1024 / 1024).toFixed(2)} GB / {(downloadProgress.total / 1024 / 1024 / 1024).toFixed(2)} GB
                              </>
                            ) : (
                              "Waiting for progress..."
                            )}
                          </span>
                          <span>{formatEta(downloadProgress)}</span>
                        </div>
                        {downloadProgress.error && (
                          <p className="text-[11px] text-red-300">{downloadProgress.error}</p>
                        )}
                        <div className="flex gap-2">
                          {(downloadProgress.status === "queued" || downloadProgress.status === "running") && (
                            <Button variant="secondary" size="sm" onClick={() => cancelDownload(model.name)} className="gap-2">
                              <Pause className="h-3.5 w-3.5" />
                              Cancel
                            </Button>
                          )}
                          {(downloadProgress.status === "cancelled" || downloadProgress.status === "failed") && (
                            <Button variant="secondary" size="sm" onClick={() => resumeDownload(model.name)} className="gap-2">
                              <Download className="h-3.5 w-3.5" />
                              Resume
                            </Button>
                          )}
                        </div>
                      </div>
                    ) : model.is_installed ? (
                      <Button disabled className="w-full border border-cortex-success/30 bg-cortex-success/10 text-cortex-success">
                        Installed
                      </Button>
                    ) : (
                      <Button onClick={() => handleDownload(model.name)} className="w-full gap-2">
                        <Download className="h-4 w-4" />
                        Pull local model
                      </Button>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-cortex-border py-20 text-center">
            <p className="text-base font-semibold text-cortex-text">No models found</p>
            <p className="mt-2 text-sm text-cortex-muted">Try a different search term or filter.</p>
          </div>
        )}
      </div>
    </div>
  );
}
