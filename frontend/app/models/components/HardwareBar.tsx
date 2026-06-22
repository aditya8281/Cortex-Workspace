"use client";

import type { HardwareProfile } from "@/shared/types";

interface HardwareBarProps {
  hardware: HardwareProfile;
  activeDownloads: number;
}

export default function HardwareBar({ hardware, activeDownloads }: HardwareBarProps) {
  const gpu = hardware.gpu;
  const ramUsed = hardware.ram_gb - hardware.ram_available_gb;
  const ramPercent = Math.round((ramUsed / hardware.ram_gb) * 100);

  return (
    <div className="glass-panel rounded-xl px-5 py-3 flex items-center gap-8 mb-6">
      <div className="flex items-center gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">GPU</div>
          <div className="text-[13px] font-medium">{gpu.available ? gpu.name : "No GPU"} · {gpu.vram_gb} GB</div>
        </div>
      </div>

      <div className="w-px h-6 bg-white/[0.06]" />

      <div className="flex items-center gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">RAM</div>
          <div className="text-[13px] font-medium">{ramUsed}/{hardware.ram_gb} GB</div>
        </div>
        <div className="w-[60px] h-1 bg-surface rounded-full overflow-hidden">
          <div className="h-full bg-accent rounded-full" style={{ width: `${ramPercent}%` }} />
        </div>
      </div>

      <div className="w-px h-6 bg-white/[0.06]" />

      <div>
        <div className="font-mono text-[10px] uppercase tracking-wider text-muted">Disk</div>
        <div className="text-[13px] font-medium">{hardware.disk_free_gb} GB free</div>
      </div>

      <div className="w-px h-6 bg-white/[0.06]" />

      {hardware.supports_cuda && (
        <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-success/10 text-success border border-success/20">
          CUDA
        </span>
      )}
      {hardware.supports_metal && (
        <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-success/10 text-success border border-success/20">
          Metal
        </span>
      )}

      {activeDownloads > 0 && (
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <span className="font-mono text-[11px] text-accent">{activeDownloads} downloading</span>
        </div>
      )}
    </div>
  );
}
