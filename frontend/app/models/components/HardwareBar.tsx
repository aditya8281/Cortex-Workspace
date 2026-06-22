"use client";

import type { HardwareProfile, SystemMetrics } from "@/shared/types";

interface HardwareBarProps {
  hardware: HardwareProfile;
  activeDownloads: number;
  liveMetrics?: SystemMetrics | null;
}

export default function HardwareBar({ hardware, activeDownloads, liveMetrics }: HardwareBarProps) {
  const gpu = hardware.gpu;
  const ramUsed = liveMetrics?.ram_used_gb ?? (hardware.ram_gb - hardware.ram_available_gb);
  const ramPercent = liveMetrics?.ram_percent ?? Math.round((ramUsed / hardware.ram_gb) * 100);
  const vramUsed = liveMetrics?.gpu_percent != null ? Math.round((liveMetrics.gpu_percent / 100) * gpu.vram_gb) : null;
  const vramPercent = liveMetrics?.gpu_percent ?? null;

  return (
    <div className="glass-panel rounded-xl px-5 py-3 flex items-center gap-8 mb-6">
      <div className="flex items-center gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">GPU</div>
          <div className="text-[13px] font-medium">{gpu.available ? gpu.name : "No GPU"} · {gpu.vram_gb} GB</div>
        </div>
      </div>

      {vramPercent != null && (
        <>
          <div className="w-px h-6 bg-white/[0.06]" />
          <div className="flex items-center gap-2">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-wider text-muted">VRAM</div>
              <div className="text-[13px] font-medium">{vramUsed}/{gpu.vram_gb} GB</div>
            </div>
            <div className="w-[60px] h-1 bg-surface rounded-full overflow-hidden">
              <div className="h-full bg-purple-500 rounded-full transition-all duration-300" style={{ width: `${vramPercent}%` }} />
            </div>
          </div>
        </>
      )}

      <div className="w-px h-6 bg-white/[0.06]" />

      <div className="flex items-center gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">RAM</div>
          <div className="text-[13px] font-medium">{Math.round(ramUsed * 10) / 10}/{hardware.ram_gb} GB</div>
        </div>
        <div className="w-[60px] h-1 bg-surface rounded-full overflow-hidden">
          <div className="h-full bg-accent rounded-full transition-all duration-300" style={{ width: `${ramPercent}%` }} />
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
