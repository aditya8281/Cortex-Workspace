"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  Download,
  HardDrive,
  Settings,
  RefreshCw,
  LayoutGrid,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import Card from "@/shared/ui/Card";
import Button from "@/shared/ui/Button";
import { TabGroup, TabPanel } from "@/shared/ui/TabGroup";
import { useAuth } from "@/shared/auth/AuthProvider";
import { modelsApi } from "@/shared/api";
import HardwareOverview from "./HardwareOverview";
import WorkloadRecommendations from "./WorkloadRecommendations";
import ModelBrowser from "./ModelBrowser";
import InstalledModelsPanel from "./InstalledModelsPanel";
import DownloadQueuePanel from "./DownloadQueuePanel";
import type { HardwareProfile, WorkloadRecommendations as WorkloadRecs } from "@/shared/types";

export default function ModelsPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [workloads, setWorkloads] = useState<Record<string, WorkloadRecs>>({});
  const [loadingRecs, setLoadingRecs] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    modelsApi
      .recommendedEnhanced()
      .then((data) => {
        setHardware(data.hardware);
        setWorkloads(data.workloads);
      })
      .catch(() => {})
      .finally(() => setLoadingRecs(false));
  }, [user]);

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-6"
        >
          <div className="flex items-center gap-4 mb-6">
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

          {/* Hardware Overview */}
          {hardware && <HardwareOverview hardware={hardware} />}
        </motion.div>

        {/* Content Tabs */}
        <TabGroup
          tabs={[
            { id: "recommended", label: "Recommended", icon: <Brain size={14} /> },
            { id: "installed", label: "Installed", icon: <HardDrive size={14} /> },
            { id: "browse", label: "Browse All", icon: <LayoutGrid size={14} /> },
            { id: "downloads", label: "Downloads", icon: <Download size={14} /> },
            { id: "settings", label: "Settings", icon: <Settings size={14} /> },
          ]}
        >
          <TabPanel tabId="recommended">
            {loadingRecs ? (
              <div className="space-y-6">
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
            ) : (
              <WorkloadRecommendations workloads={workloads} />
            )}
          </TabPanel>

          <TabPanel tabId="installed">
            <InstalledModelsPanel />
          </TabPanel>

          <TabPanel tabId="browse">
            <ModelBrowser />
          </TabPanel>

          <TabPanel tabId="downloads">
            <DownloadQueuePanel />
          </TabPanel>

          <TabPanel tabId="settings">
            <div className="space-y-6">
              <Card className="p-6" gradient>
                <h3 className="text-sm font-semibold text-text mb-4">Inference Backend</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 text-sm text-text-secondary">
                    <input type="radio" name="backend" value="auto" defaultChecked className="accent-accent" />
                    Auto (recommended)
                  </label>
                  <label className="flex items-center gap-3 text-sm text-text-secondary">
                    <input type="radio" name="backend" value="ollama" className="accent-accent" />
                    Ollama
                  </label>
                  <label className="flex items-center gap-3 text-sm text-text-secondary">
                    <input type="radio" name="backend" value="llama_cpp" className="accent-accent" />
                    llama.cpp
                  </label>
                </div>
              </Card>

              <Card className="p-6" gradient>
                <h3 className="text-sm font-semibold text-text mb-4">Catalogue</h3>
                <p className="text-xs text-text-secondary mb-4">
                  Refresh the model catalogue from Ollama and HuggingFace.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => modelsApi.refreshCatalogue()}
                >
                  <RefreshCw size={14} /> Refresh Catalogue
                </Button>
              </Card>

              <Card className="p-6" gradient>
                <h3 className="text-sm font-semibold text-text mb-4">HuggingFace API</h3>
                <p className="text-xs text-text-secondary mb-4">
                  Optional: Add your HuggingFace API token for higher rate limits when discovering GGUF models.
                </p>
                <input
                  type="password"
                  placeholder="hf_..."
                  className="w-full h-10 px-4 rounded-xl bg-bg-surface border border-border-subtle text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 transition-colors"
                />
                <p className="text-xs text-text-muted mt-2">
                  Token is stored locally and never sent to Cortex servers.
                </p>
              </Card>
            </div>
          </TabPanel>
        </TabGroup>
      </div>
    </DashboardShell>
  );
}
