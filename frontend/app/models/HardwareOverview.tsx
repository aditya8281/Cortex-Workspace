"use client";

import { motion } from "framer-motion";
import { Cpu, HardDrive, Activity, Zap } from "lucide-react";
import Card from "@/shared/ui/Card";
import { MetricRing } from "@/shared/ui/MetricRing";
import type { HardwareProfile } from "@/shared/types";

interface HardwareOverviewProps {
  hardware: HardwareProfile;
}

export default function HardwareOverview({ hardware }: HardwareOverviewProps) {
  const ramUsedPercent = hardware.ram_percent;
  const gpu = hardware.gpu;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="mb-8"
    >
      <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 mb-4">
        {/* RAM Ring */}
        <MetricRing
          label="RAM"
          value={ramUsedPercent}
          color="#8b5cf6"
          unit={`${hardware.ram_gb}GB`}
        />

        {/* GPU Card */}
        <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4 min-w-[140px]" gradient>
          {gpu.available ? (
            <>
              <Zap size={20} className="text-accent" />
              <span className="micro-label">GPU</span>
              <span className="text-sm text-text text-center leading-tight">
                {gpu.name || "Unknown"}
              </span>
              <span className="text-xs text-text-muted">
                {gpu.vram_gb.toFixed(1)}GB VRAM
              </span>
              {gpu.memory_bandwidth_gbps && (
                <span className="text-xs text-text-muted">
                  {gpu.memory_bandwidth_gbps.toFixed(0)} GB/s
                </span>
              )}
            </>
          ) : (
            <>
              <Cpu size={20} className="text-text-muted" />
              <span className="micro-label">GPU</span>
              <span className="text-sm text-text-secondary">No GPU</span>
            </>
          )}
        </Card>

        {/* CPU Card */}
        <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4 min-w-[120px]" gradient>
          <Cpu size={20} className="text-accent" />
          <span className="micro-label">CPU</span>
          <span className="text-sm text-text">{hardware.cpu_threads} threads</span>
          <span className="text-xs text-text-muted">
            {hardware.cpu_freq_mhz > 0 ? `${(hardware.cpu_freq_mhz / 1000).toFixed(1)} GHz` : hardware.cpu_arch}
          </span>
        </Card>

        {/* Disk Card */}
        <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4 min-w-[120px]" gradient>
          <HardDrive size={20} className="text-accent" />
          <span className="micro-label">Disk Free</span>
          <span className="text-sm text-text">{hardware.disk_free_gb.toFixed(0)}GB</span>
        </Card>
      </div>

      {/* Backend indicators */}
      <div className="flex items-center justify-center gap-4 text-xs text-text-muted">
        {hardware.supports_cuda && (
          <span className="flex items-center gap-1">
            <Activity size={12} className="text-success" />
            CUDA
          </span>
        )}
        {hardware.supports_metal && (
          <span className="flex items-center gap-1">
            <Activity size={12} className="text-success" />
            Metal
          </span>
        )}
        {gpu.compute_capability && (
          <span>Compute {gpu.compute_capability}</span>
        )}
        {gpu.arch && (
          <span className="capitalize">{gpu.arch.replace("_", " ")}</span>
        )}
      </div>
    </motion.div>
  );
}
