"use client";

import type { HardwareInfo } from "../api";

interface HardwareBarProps {
  hardware: HardwareInfo | null;
  loading?: boolean;
}

export function HardwareBar({ hardware, loading }: HardwareBarProps) {
  if (loading) {
    return (
      <div className="flex items-center gap-4 rounded-lg bg-bg-surface px-4 py-2.5 animate-pulse">
        <div className="h-4 w-20 rounded bg-bg-elevated" />
        <div className="h-4 w-24 rounded bg-bg-elevated" />
        <div className="h-4 w-16 rounded bg-bg-elevated" />
        <div className="h-4 w-24 rounded bg-bg-elevated" />
      </div>
    );
  }

  if (!hardware) return null;

  const gpuKeys = Object.keys(hardware.gpu ?? {});
  const gpuLabel =
    gpuKeys.length > 0
      ? `${gpuKeys.length} GPU${gpuKeys.length > 1 ? "s" : ""}`
      : "No GPU";

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg bg-bg-surface px-4 py-2.5 text-xs text-text-muted">
      {/* RAM */}
      <span className="inline-flex items-center gap-1.5" title={`${hardware.ram_gb} GB total, ${hardware.ram_available_gb} GB available`}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-text-muted shrink-0">
          <rect x="1" y="2" width="10" height="8" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M4 2v8M8 2v8" stroke="currentColor" strokeWidth="1.2" />
        </svg>
        <span className="tabular-nums">{hardware.ram_gb} GB</span>
        <span
          className={`tabular-nums ${
            hardware.ram_percent > 80
              ? "text-danger"
              : hardware.ram_percent > 50
                ? "text-warning"
                : "text-text-muted"
          }`}
        >
          ({hardware.ram_percent}% used)
        </span>
      </span>

      <span className="text-border-subtle hidden sm:inline">|</span>

      {/* CPU */}
      <span className="inline-flex items-center gap-1.5" title={`${hardware.cpu_arch} — ${hardware.cpu_count} cores / ${hardware.cpu_threads} threads`}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-text-muted shrink-0">
          <rect x="2" y="2" width="8" height="8" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M2 4.5H.5M2 7.5H.5M11.5 4.5H10M11.5 7.5H10M4.5 2V.5M7.5 2V.5M4.5 11.5V10M7.5 11.5V10" stroke="currentColor" strokeWidth="1.2" />
        </svg>
        <span className="tabular-nums">{hardware.cpu_count}C</span>
        <span className="hidden sm:inline">/</span>
        <span className="hidden sm:inline tabular-nums">{hardware.cpu_threads}T</span>
        <span className="hidden sm:inline text-text-muted">
          {" "}· {hardware.cpu_freq_mhz > 1000 ? `${(hardware.cpu_freq_mhz / 1000).toFixed(1)} GHz` : `${hardware.cpu_freq_mhz} MHz`}
        </span>
      </span>

      <span className="text-border-subtle hidden sm:inline">|</span>

      {/* GPU */}
      <span className="inline-flex items-center gap-1.5" title={JSON.stringify(hardware.gpu, null, 2)}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-text-muted shrink-0">
          <rect x="1" y="3" width="10" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <circle cx="4" cy="6" r="1.5" fill="currentColor" />
          <rect x="6.5" y="4.5" width="3" height="3" rx="0.5" fill="currentColor" />
        </svg>
        <span>{gpuLabel}</span>
        {hardware.supports_cuda && <span className="text-accent">CUDA</span>}
        {hardware.supports_metal && <span className="text-accent">Metal</span>}
      </span>

      <span className="text-border-subtle hidden sm:inline">|</span>

      {/* Disk */}
      <span className="inline-flex items-center gap-1.5">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-text-muted shrink-0">
          <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <circle cx="6" cy="6" r="2" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M6 1v2M6 9v2M1 6h2M9 6h2" stroke="currentColor" strokeWidth="1.2" />
        </svg>
        <span className="tabular-nums">{hardware.disk_free_gb} GB free</span>
      </span>
    </div>
  );
}
