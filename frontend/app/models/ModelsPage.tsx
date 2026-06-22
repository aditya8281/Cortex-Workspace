"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertTriangle, Brain, RefreshCw } from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import Card from "@/shared/ui/Card";
import Button from "@/shared/ui/Button";
import HardwareBar from "./components/HardwareBar";
import TopPicksCarousel from "./components/TopPicksCarousel";
import WorkloadColumns from "./components/WorkloadColumns";
import CatalogTable from "./components/CatalogTable";
import InstalledBar from "./components/InstalledBar";
import { useAuth } from "@/shared/auth/AuthProvider";
import { modelsApi } from "@/shared/api";
import { useSystemWebSocket } from "@/shared/hooks/useSystemWebSocket";
import { useLiveMetrics } from "@/shared/hooks/useLiveMetrics";
import type {
  CatalogStatus,
  HardwareProfile,
  WorkloadRecommendations as WorkloadRecs,
  ModelInfo,
  SystemMetrics,
} from "@/shared/types";

function CatalogStatusBanner({ status }: { status?: CatalogStatus }) {
  if (!status) return null;

  const isDegraded =
    status.from_fallback ||
    status.cloud !== "ok" ||
    status.registry !== "ok";

  if (!isDegraded) return null;

  const issues: string[] = [];
  if (status.from_fallback) issues.push("Using cached catalog (all sources unavailable)");
  if (status.cloud !== "ok") issues.push(`Cloud: ${status.cloud}`);
  if (status.registry !== "ok") issues.push(`Registry: ${status.registry}`);

  return (
    <div className="glass-panel rounded-xl px-4 py-2 mb-4 border border-warning/20 bg-warning/5">
      <div className="flex items-center gap-2 text-[11px] text-warning">
        <AlertTriangle size={14} />
        <span>Catalog degraded — {issues.join("; ")}</span>
      </div>
    </div>
  );
}

export default function ModelsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const liveMetrics = useLiveMetrics();
  const [workloads, setWorkloads] = useState<Record<string, WorkloadRecs>>({});
  const [allModels, setAllModels] = useState<ModelInfo[]>([]);
  const [installedModels, setInstalledModels] = useState<Array<{ model_id: string; display_name: string; variant: string; size_gb: number; last_used: string; usage_count: number }>>([]);

  const [catalogStatus, setCatalogStatus] = useState<CatalogStatus | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());
  const [refreshKey, setRefreshKey] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    async function load() {
      try {
        const [recsData, listData, instData] = await Promise.all([
          modelsApi.recommendedEnhanced(),
          modelsApi.list(),
          modelsApi.installed(),
        ]);
        if (cancelled) return;
        setHardware(recsData.hardware);
        setWorkloads(recsData.workloads);
        setAllModels(listData.models);
        setCatalogStatus(listData.catalog_status);
        setInstalledModels((instData.models || []).map((m) => ({
          model_id: m.model_id,
          display_name: m.display_name,
          variant: m.variants?.[0]?.quantization || "default",
          size_gb: m.variants?.[0]?.size_gb || 0,
          last_used: "—",
          usage_count: 0,
        })));
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load models");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [user, refreshKey]);

  const handleDownload = async (modelName: string, variant?: string) => {
    try {
      const res = await modelsApi.download(modelName, variant);
      const key = res.download_id || modelName;
      setDownloadingModels((prev) => new Set(prev).add(key));
      setDownloadProgress((prev) => new Map(prev).set(key, 0));
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  const handleCancel = async (modelName: string) => {
    try {
      await modelsApi.cancel(modelName);
      setDownloadingModels((prev) => {
        const n = new Set(prev);
        n.delete(modelName);
        return n;
      });
      setDownloadProgress((prev) => {
        const n = new Map(prev);
        n.delete(modelName);
        return n;
      });
    } catch (err) {
      console.error("Cancel failed:", err);
    }
  };

  const handleScan = async () => {
    setSyncing(true);
    try {
      await Promise.all([
        modelsApi.refreshCatalogue(),
        modelsApi.syncInstalled(),
      ]);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      console.error("Scan failed:", err);
    } finally {
      setSyncing(false);
    }
  };

  useSystemWebSocket({
    path: "/ws/models",
    enabled: downloadingModels.size > 0,
    onMessage(event) {
      const data = JSON.parse(event.data);
      if (data.type === "model_progress" && Array.isArray(data.models)) {
        for (const m of data.models) {
          setDownloadProgress((prev) => new Map(prev).set(m.name, m.progress));
          if (m.progress >= 1.0) {
            setDownloadingModels((prev) => {
              const n = new Set(prev);
              n.delete(m.name);
              return n;
            });
            setRefreshKey((k) => k + 1);
          }
        }
      }
    },
  });

  const topRecs = useMemo(() => {
    const all = Object.values(workloads).flatMap((w) => w.recommendations);
    return all.sort((a, b) => b.score - a.score).slice(0, 5);
  }, [workloads]);

  if (authLoading || !user) return null;

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-6"
        >
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
              <Brain size={24} className="text-accent" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-text">Models</h1>
              <p className="text-sm text-text-secondary">
                Browse, download, and manage LLM models for your agents
              </p>
            </div>
          </div>
        </motion.div>

        {/* Catalog Status Banner */}
        <CatalogStatusBanner status={catalogStatus} />

        {/* Hardware Status Bar */}
        {hardware && (
          <HardwareBar hardware={hardware} activeDownloads={downloadingModels.size} liveMetrics={liveMetrics} />
        )}

        {/* Loading State */}
        {loading && (
          <div className="space-y-6 mt-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <div className="h-6 w-48 rounded bg-bg-surface shimmer-bg" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <div key={j} className="h-48 rounded-xl bg-bg-surface shimmer-bg" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <Card className="p-8 text-center mt-6">
            <p className="text-sm text-text-secondary mb-4">{error}</p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setError(null);
                setLoading(true);
                setRefreshKey((k) => k + 1);
              }}
            >
              <RefreshCw size={14} /> Retry
            </Button>
          </Card>
        )}

        {/* Main Content */}
        {!loading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.15 }}
            className="space-y-8 mt-6"
          >
            {/* Top Picks Carousel */}
            {topRecs.length > 0 && (
              <TopPicksCarousel
                recommendations={topRecs}
                onDownload={handleDownload}
              />
            )}

            {/* Workload Columns */}
            <WorkloadColumns
              workloads={workloads}
              onDownload={handleDownload}
            />

            {/* Catalog Table */}
            <CatalogTable
              models={allModels}
              onDownload={handleDownload}
              hardware={hardware}
            />

            {/* Installed Bar */}
            <InstalledBar
              models={installedModels}
              onManage={() => router.push("/settings")}
              onChat={(modelId) => router.push(`/chat?model=${modelId}`)}
              onDelete={async (modelId) => {
                try {
                  await modelsApi.delete(modelId);
                  setRefreshKey((k) => k + 1);
                } catch (err) {
                  console.error("Delete failed:", err);
                }
              }}
              onScan={handleScan}
              scanning={syncing}
            />
          </motion.div>
        )}
      </div>
    </DashboardShell>
  );
}
