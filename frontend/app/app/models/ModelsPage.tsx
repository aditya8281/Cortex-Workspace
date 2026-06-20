"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  Cpu,
  HardDrive,
  Activity,
  RefreshCw,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import Card from "@/shared/ui/Card";
import { MetricRing } from "@/shared/ui/MetricRing";
import { TabGroup, TabPanel } from "@/shared/ui/TabGroup";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import { useAuth } from "@/shared/auth/AuthProvider";
import { modelsApi } from "@/shared/api";
import ModelBrowser from "./ModelBrowser";
import type { HardwareInfo, ModelInfo } from "@/shared/types";

export default function ModelsPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [recommendedModels, setRecommendedModels] = useState<ModelInfo[]>([]);
  const [loadingRecommended, setLoadingRecommended] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    modelsApi
      .recommended()
      .then((data) => {
        setHardware(data.hardware);
        setRecommendedModels(data.recommended);
      })
      .catch(() => {})
      .finally(() => setLoadingRecommended(false));
  }, [user]);

  if (loading || !user) return null;

  const ramUsedPercent = hardware
    ? Math.round((hardware.ram_gb * 0.6) / hardware.ram_gb * 100)
    : 0;

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-8"
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
          {hardware && (
            <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12 mb-4">
              <MetricRing
                label="RAM"
                value={ramUsedPercent}
                color="#8b5cf6"
                unit={`${hardware.ram_gb}GB`}
              />
              <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4" gradient>
                <Cpu size={20} className="text-accent" />
                <span className="micro-label">CPU Cores</span>
                <span className="text-sm text-text">{hardware.cpu_count}</span>
              </Card>
              <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4" gradient>
                <HardDrive size={20} className="text-accent" />
                <span className="micro-label">GPU</span>
                <span className="text-sm text-text text-center">
                  {hardware.gpu.available ? hardware.gpu.name : "No GPU"}
                </span>
                {hardware.gpu.available && (
                  <span className="text-xs text-text-muted">
                    {hardware.gpu.vram_gb.toFixed(1)}GB VRAM
                  </span>
                )}
              </Card>
              <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4" gradient>
                <Activity size={20} className="text-accent" />
                <span className="micro-label">Models</span>
                <span className="text-sm text-text">
                  {recommendedModels.length} recommended
                </span>
              </Card>
            </div>
          )}
        </motion.div>

        {/* Content */}
        <TabGroup
          tabs={[
            { id: "browse", label: "Browse All" },
            { id: "recommended", label: "Recommended", icon: <Brain size={14} /> },
          ]}
        >
          <TabPanel tabId="browse">
            <ModelBrowser />
          </TabPanel>

          <TabPanel tabId="recommended">
            {loadingRecommended ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-64 rounded-xl bg-bg-surface shimmer-bg"
                  />
                ))}
              </div>
            ) : recommendedModels.length === 0 ? (
              <Card className="p-8 text-center" gradient>
                <Brain size={40} className="text-text-muted mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-text mb-2">
                  No recommendations available
                </h3>
                <p className="text-sm text-text-secondary max-w-md mx-auto">
                  Hardware detection could not determine suitable models.
                  Try browsing all models instead.
                </p>
              </Card>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-text-secondary">
                    Based on your hardware ({hardware?.ram_gb ?? "?"}GB RAM
                    {hardware?.gpu.available ? `, ${hardware.gpu.name}` : ""})
                  </p>
                </div>
                <ModelBrowser />
              </div>
            )}
          </TabPanel>
        </TabGroup>
      </div>
    </DashboardShell>
  );
}
