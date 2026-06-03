import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/stores/appStore";
import { cn } from "@/lib/utils";
import {
  getMarketplace,
  getHardwareInfo,
  pullModel,
  type MarketplaceModel
} from "@/api/ai";
import {
  Download,
  Cpu,
  Search,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  HardDrive,
  Clock,
  Database,
  Activity,
  Info,
  ArrowRight,
  Loader2
} from "lucide-react";

export function MarketplacePage() {
  const qc = useQueryClient();
  const setToast = useAppStore((s) => s.setToast);

  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "coding" | "chat" | "small" | "installed">("all");

  // Track active downloads: model_name -> progress info
  const [downloads, setDownloads] = useState<Record<string, {
    percent: number;
    status: string;
    completed?: number;
    total?: number;
    error?: string;
  }>>({});

  // Query hardware detection
  const { data: hardware, isLoading: loadingHardware } = useQuery({
    queryKey: ["hardwareInfo"],
    queryFn: getHardwareInfo,
    refetchInterval: 15000, // refresh resource metrics every 15s
  });

  // Query marketplace catalog
  const { data: catalog = [], isLoading: loadingCatalog } = useQuery<MarketplaceModel[]>({
    queryKey: ["marketplace"],
    queryFn: getMarketplace,
  });

  const handleDownload = async (modelName: string) => {
    try {
      setDownloads((prev) => ({
        ...prev,
        [modelName]: { percent: 0, status: "Connecting..." }
      }));

      await pullModel(modelName, (prog) => {
        setDownloads((prev) => ({
          ...prev,
          [modelName]: {
            percent: prog.percent,
            status: prog.status || "Downloading...",
            completed: prog.completed,
            total: prog.total
          }
        }));
      });

      setDownloads((prev) => ({
        ...prev,
        [modelName]: { percent: 100, status: "Completed" }
      }));
      setToast(`Successfully downloaded ${modelName}`);
      qc.invalidateQueries({ queryKey: ["marketplace"] });
      qc.invalidateQueries({ queryKey: ["models"] });
    } catch (err: any) {
      console.error(err);
      setDownloads((prev) => ({
        ...prev,
        [modelName]: { percent: 0, status: "Failed", error: err.message || "Unknown error" }
      }));
      setToast(`Failed to pull ${modelName}: ${err.message || "Unknown error"}`);
    }
  };

  // Filter & Search Logic
  const filteredCatalog = catalog.filter((model) => {
    // 1. Search Query
    const matchesSearch =
      model.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.best_use_case.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.name.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    // 2. Tab Filter
    if (activeFilter === "all") return true;
    if (activeFilter === "installed") return model.is_installed;
    if (activeFilter === "coding") return model.tags.includes("Coding");
    if (activeFilter === "chat") return model.tags.includes("Chat");
    if (activeFilter === "small") return model.vram_requirement_gb <= 5;

    return true;
  });

  // Smart Recommendations
  const getSmartRecommendations = () => {
    if (!hardware) return [];
    
    const detectedVram = hardware.gpu.detected ? hardware.gpu.total_vram_gb : 0;
    const systemRam = hardware.ram.total_gb;
    
    // Determine recommendation based on VRAM/RAM limits
    return catalog.filter((model) => {
      // Don't recommend already installed models
      if (model.is_installed) return false;

      if (detectedVram > 0) {
        // GPU detected: Recommend models that fit in VRAM with at least 1GB headroom
        return model.vram_requirement_gb <= (detectedVram - 0.5);
      } else {
        // CPU/RAM only: Recommend small models that fit in RAM
        return model.vram_requirement_gb <= 4 && systemRam >= 8;
      }
    }).slice(0, 3); // pick top 3 matching
  };

  const recommendations = getSmartRecommendations();

  return (
    <div className="container mx-auto space-y-8 p-6 max-w-7xl">
      {/* Header section with styling */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-cortex-accent to-cortex-success bg-clip-text text-transparent">
          Model Marketplace
        </h1>
        <p className="text-cortex-muted text-sm max-w-2xl">
          Browse and install optimized LLM models directly to your machine. All models run 100% locally through Ollama, protecting your privacy and workspace data.
        </p>
      </div>

      {/* Hardware Detection Banner */}
      <Card className="border-cortex-border bg-gradient-to-br from-cortex-surface/60 to-cortex-surface/20 backdrop-blur-md shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-cortex-accent/5 rounded-full blur-3xl -z-10" />
        <CardHeader className="pb-4">
          <CardTitle className="text-lg flex items-center gap-2 text-cortex-text">
            <Cpu className="h-5 w-5 text-cortex-accent animate-pulse" />
            Hardware Architecture Auto-Detection
          </CardTitle>
          <CardDescription>
            Cortex continuously scans your local compute capability to match suitable models.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingHardware ? (
            <div className="flex justify-center items-center py-6">
              <Loader2 className="h-8 w-8 text-cortex-accent animate-spin" />
            </div>
          ) : hardware ? (
            <div className="grid gap-6 md:grid-cols-4">
              <div className="space-y-1.5 p-4 rounded-xl bg-cortex-elevated/40 border border-cortex-border/50">
                <span className="text-xs font-semibold text-cortex-muted uppercase tracking-wider block">Operating System</span>
                <span className="text-sm font-bold text-cortex-text block truncate">{hardware.os}</span>
                <span className="text-[10px] text-cortex-muted block">Native Environment</span>
              </div>
              <div className="space-y-1.5 p-4 rounded-xl bg-cortex-elevated/40 border border-cortex-border/50">
                <span className="text-xs font-semibold text-cortex-muted uppercase tracking-wider block">CPU Core</span>
                <span className="text-sm font-bold text-cortex-text block truncate" title={hardware.cpu}>{hardware.cpu}</span>
                <span className="text-[10px] text-cortex-muted block">System Processing Unit</span>
              </div>
              <div className="space-y-1.5 p-4 rounded-xl bg-cortex-elevated/40 border border-cortex-border/50">
                <span className="text-xs font-semibold text-cortex-muted uppercase tracking-wider block">System Memory (RAM)</span>
                <span className="text-sm font-bold text-cortex-text block">
                  {hardware.ram.total_gb} GB <span className="text-xs text-cortex-muted">({hardware.ram.available_gb} GB avail)</span>
                </span>
                <div className="w-full bg-cortex-border rounded-full h-1.5 mt-2">
                  <div
                    className="bg-cortex-accent h-1.5 rounded-full"
                    style={{ width: `${hardware.ram.usage_percent}%` }}
                  />
                </div>
              </div>
              <div className="space-y-1.5 p-4 rounded-xl bg-cortex-elevated/40 border border-cortex-border/50">
                <span className="text-xs font-semibold text-cortex-muted uppercase tracking-wider block">Graphics Processor (GPU)</span>
                {hardware.gpu.detected ? (
                  <>
                    <span className="text-sm font-bold text-cortex-success block truncate" title={hardware.gpu.name}>
                      {hardware.gpu.name}
                    </span>
                    <span className="text-[10px] text-cortex-muted block">
                      VRAM: {hardware.gpu.total_vram_gb} GB total
                    </span>
                    <div className="w-full bg-cortex-border rounded-full h-1.5 mt-2">
                      <div
                        className="bg-cortex-success h-1.5 rounded-full"
                        style={{ width: `${hardware.gpu.utilization}%` }}
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <span className="text-sm font-bold text-cortex-warn block">CPU Only Mode</span>
                    <span className="text-[10px] text-cortex-muted block">No compatible CUDA GPU detected</span>
                    <div className="h-1.5 mt-2 bg-cortex-warn/10 rounded-full" />
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="text-sm text-cortex-muted py-2">Failed to load hardware specifications.</div>
          )}
        </CardContent>
      </Card>

      {/* Smart Recommendations Section */}
      {hardware && recommendations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-cortex-accent" />
            <h2 className="text-xl font-semibold text-cortex-text">Hardware-Matched Recommendations</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {recommendations.map((model) => (
              <Card key={`rec-${model.name}`} className="border-cortex-accent/40 bg-cortex-surface/40 hover:border-cortex-accent transition duration-200 shadow-lg">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="accent" className="bg-cortex-accent-soft text-cortex-accent border-none text-[10px]">
                      Recommended For You
                    </Badge>
                    <span className="text-xs text-cortex-muted">{model.size}</span>
                  </div>
                  <CardTitle className="text-base mt-2 text-cortex-text">{model.display_name}</CardTitle>
                  <CardDescription className="text-xs line-clamp-1">{model.best_use_case}</CardDescription>
                </CardHeader>
                <CardContent className="pt-2 flex flex-col justify-between h-[100px]">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1 text-cortex-muted">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{model.context_length >= 1000 ? `${model.context_length / 1024}k` : model.context_length} Context</span>
                    </div>
                    <div className="flex items-center gap-1 text-cortex-muted">
                      <Database className="h-3.5 w-3.5" />
                      <span>{model.vram_requirement_gb} GB VRAM</span>
                    </div>
                  </div>
                  
                  {/* Download button / progress */}
                  <div className="mt-4">
                    {downloads[model.name] ? (
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px]">
                          <span className="text-cortex-muted truncate max-w-[120px]">{downloads[model.name].status}</span>
                          <span className="text-cortex-accent font-bold">{downloads[model.name].percent}%</span>
                        </div>
                        <div className="w-full bg-cortex-border rounded-full h-1">
                          <div
                            className="bg-cortex-accent h-1 rounded-full transition-all duration-300"
                            style={{ width: `${downloads[model.name].percent}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        className="w-full bg-cortex-accent hover:bg-cortex-accent/80 text-cortex-bg font-bold flex items-center gap-1.5"
                        onClick={() => handleDownload(model.name)}
                      >
                        <Download className="h-3.5 w-3.5" />
                        Quick Install
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Main Catalog & Search / Filter */}
      <div className="space-y-6 pt-2">
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
          {/* Tabs */}
          <div className="flex flex-wrap gap-1.5 bg-cortex-elevated/60 p-1 rounded-xl border border-cortex-border">
            {[
              { id: "all", label: "All Models" },
              { id: "coding", label: "Coding" },
              { id: "chat", label: "General Chat" },
              { id: "small", label: "Low Resource (< 6GB VRAM)" },
              { id: "installed", label: "Installed" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveFilter(tab.id as any)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-lg transition duration-150 cursor-pointer",
                  activeFilter === tab.id
                    ? "bg-cortex-accent text-cortex-bg font-bold shadow-md"
                    : "text-cortex-muted hover:text-cortex-text"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search bar */}
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-cortex-muted" />
            <Input
              placeholder="Search local models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-cortex-surface/40 border-cortex-border text-cortex-text focus-visible:ring-cortex-accent focus-visible:border-cortex-accent placeholder:text-cortex-muted/60 text-xs rounded-xl"
            />
          </div>
        </div>

        {/* Loading Catalog State */}
        {loadingCatalog ? (
          <div className="flex flex-col justify-center items-center py-20 gap-4">
            <Loader2 className="h-10 w-10 text-cortex-accent animate-spin" />
            <p className="text-sm text-cortex-muted">Retrieving curated model library...</p>
          </div>
        ) : filteredCatalog.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-3">
            {filteredCatalog.map((model) => {
              // Warning if model VRAM requirements exceed detected VRAM
              const detectedVram = hardware?.gpu.detected ? hardware.gpu.total_vram_gb : 0;
              const isVramTooLow = hardware?.gpu.detected && model.vram_requirement_gb > detectedVram;
              const isCpuOnlyWarning = !hardware?.gpu.detected && model.vram_requirement_gb >= 6;
              const showWarning = isVramTooLow || isCpuOnlyWarning;

              const downloadProgress = downloads[model.name];

              return (
                <Card
                  key={model.name}
                  className={cn(
                    "border-cortex-border bg-cortex-surface/40 hover:bg-cortex-surface/60 transition duration-200 flex flex-col justify-between overflow-hidden relative",
                    model.is_installed && "border-cortex-success/40"
                  )}
                >
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex flex-wrap gap-1">
                        {model.tags.map((tag) => (
                          <Badge
                            key={tag}
                            className="bg-cortex-elevated text-cortex-muted hover:bg-cortex-elevated border-none text-[9px]"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <span className="text-xs text-cortex-muted font-mono">{model.size}</span>
                    </div>

                    <CardTitle className="text-base mt-3 flex items-center justify-between text-cortex-text">
                      {model.display_name}
                      {model.is_installed && (
                        <CheckCircle2 className="h-4 w-4 text-cortex-success shrink-0" />
                      )}
                    </CardTitle>
                    <CardDescription className="text-xs min-h-[32px] mt-1 leading-relaxed line-clamp-2">
                      {model.best_use_case}
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-4 pt-0">
                    <hr className="border-cortex-border/50" />
                    
                    {/* Specs rows */}
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-[10px] text-cortex-muted uppercase tracking-wider block">Context</span>
                        <span className="font-semibold text-cortex-text block">
                          {model.context_length >= 1000 ? `${model.context_length / 1024}k` : model.context_length} tokens
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-cortex-muted uppercase tracking-wider block">Min VRAM</span>
                        <span className={cn("font-semibold block", showWarning ? "text-cortex-warn" : "text-cortex-text")}>
                          {model.vram_requirement_gb} GB VRAM
                        </span>
                      </div>
                    </div>

                    {/* VRAM Exceeded Warning */}
                    {showWarning && (
                      <div className="flex gap-2 p-2.5 rounded-lg bg-cortex-warn/10 border border-cortex-warn/25 text-[10px] text-cortex-warn leading-normal">
                        <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                        <div>
                          {isVramTooLow ? (
                            <span>
                              Exceeds detected VRAM ({detectedVram} GB). Model execution may be extremely slow or fail.
                            </span>
                          ) : (
                            <span>
                              GPU not detected. Running a {model.vram_requirement_gb}GB VRAM model on CPU will be highly latent.
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Download UI Section */}
                    <div className="pt-2">
                      {downloadProgress ? (
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-cortex-accent font-semibold flex items-center gap-1">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              {downloadProgress.status}
                            </span>
                            <span className="text-cortex-accent font-bold">{downloadProgress.percent}%</span>
                          </div>
                          
                          <div className="w-full bg-cortex-border rounded-full h-2">
                            <div
                              className="bg-cortex-accent h-2 rounded-full transition-all duration-300"
                              style={{ width: `${downloadProgress.percent}%` }}
                            />
                          </div>

                          {downloadProgress.completed !== undefined && downloadProgress.total !== undefined && downloadProgress.total > 0 && (
                            <p className="text-[10px] text-cortex-muted text-right">
                              {(downloadProgress.completed / 1024 / 1024 / 1024).toFixed(2)} GB / 
                              {(downloadProgress.total / 1024 / 1024 / 1024).toFixed(2)} GB
                            </p>
                          )}
                        </div>
                      ) : model.is_installed ? (
                        <Button
                          disabled
                          className="w-full bg-cortex-success/15 hover:bg-cortex-success/15 border border-cortex-success/30 text-cortex-success text-xs font-bold cursor-default"
                        >
                          Installed Local Model
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleDownload(model.name)}
                          className={cn(
                            "w-full text-xs font-bold transition duration-150 flex items-center justify-center gap-1.5",
                            showWarning
                              ? "bg-cortex-warn/80 hover:bg-cortex-warn text-cortex-bg"
                              : "bg-cortex-accent hover:bg-cortex-accent/80 text-cortex-bg"
                          )}
                        >
                          <Download className="h-4 w-4" />
                          Pull Local Model
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col justify-center items-center py-20 border border-dashed border-cortex-border rounded-2xl bg-cortex-surface/20">
            <Info className="h-10 w-10 text-cortex-muted mb-2 animate-bounce" />
            <h3 className="text-base font-bold text-cortex-text mb-1">No local models found</h3>
            <p className="text-xs text-cortex-muted">Try adjusting your filters or search query.</p>
          </div>
        )}
      </div>
    </div>
  );
}
