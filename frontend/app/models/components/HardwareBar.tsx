"use client";

import { Cpu, HardDrive, Zap, Activity, Download } from "lucide-react";
import type { HardwareProfile } from "@/shared/types";

interface HardwareBarProps {
  hardware: HardwareProfile;
  activeDownloads?: number;
}

export default function HardwareBar({ hardware, activeDownloads = 0 }: HardwareBarProps) {
  const gpu = hardware.gpu;

  return (
    <div className="flex items-center justify-between w-full px-5 py-2.5 bg-bg-surface border-b border-border-subtle">
      <div className="flex items-center gap-5">
        {/* GPU */}
        {gpu.available && (
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
            </span>
            <Zap className="h-3.5 w-3.5 text-text-muted" />
            <span className="text-xs text-text-secondary truncate max-w-[160px]">
              {gpu.name}
            </span>
            <span className="micro-label text-text-muted">
              {gpu.vram_gb}GB VRAM
            </span>
          </div>
        )}

        {!gpu.available && (
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-text-muted/30" />
            <Zap className="h-3.5 w-3.5 text-text-muted" />
            <span className="micro-label text-text-muted">No GPU</span>
          </div>
        )}

        {/* Divider */}
        <div className="h-4 w-px bg-border-subtle" />

        {/* RAM */}
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
          </span>
          <Cpu className="h-3.5 w-3.5 text-text-muted" />
          <span className="font-mono text-xs text-text-secondary">
            {(hardware.ram_gb - hardware.ram_available_gb).toFixed(1)}/{hardware.ram_gb}GB
          </span>
          <span className="micro-label text-text-muted">RAM</span>
        </div>

        {/* Divider */}
        <div className="h-4 w-px bg-border-subtle" />

        {/* Disk */}
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-[#06b6d4]" />
          </span>
          <HardDrive className="h-3.5 w-3.5 text-text-muted" />
          <span className="font-mono text-xs text-text-secondary">
            {hardware.disk_free_gb.toFixed(1)}GB free
          </span>
          <span className="micro-label text-text-muted">Disk</span>
        </div>

        {/* Divider */}
        <div className="h-4 w-px bg-border-subtle" />

        {/* Compute labels */}
        <div className="flex items-center gap-2">
          {hardware.supports_cuda && (
            <span className="micro-label text-success/80">CUDA</span>
          )}
          {hardware.supports_metal && (
            <span className="micro-label text-accent/80">Metal</span>
          )}
          <span className="micro-label text-text-muted">{hardware.cpu_arch}</span>
        </div>
      </div>

      {/* Active Downloads */}
      {activeDownloads > 0 && (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-accent/10 border border-accent/20">
          <Download className="h-3.5 w-3.5 text-accent animate-pulse" />
          <span className="font-mono text-xs text-accent font-medium">
            {activeDownloads}
          </span>
          <span className="micro-label text-accent/70">
            {activeDownloads === 1 ? "download" : "downloads"}
          </span>
        </div>
      )}
    </div>
  );
}
