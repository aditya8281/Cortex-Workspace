"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/shared/lib/utils";
import { BrainIcon } from "@/shared/ui/icons";

// ── Types ─────────────────────────────────────────────────────────────
type SystemStatus = "online" | "degraded" | "offline";

interface StatusData {
  status: SystemStatus;
  model: string;
  tps: number;
  vram: string;
}

interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "down";
}

const STATUS_DOT: Record<SystemStatus, string> = {
  online: "🟢",
  degraded: "🟡",
  offline: "🔴",
};

const STATUS_LABEL: Record<SystemStatus, string> = {
  online: "ONLINE",
  degraded: "DEGRADED",
  offline: "OFFLINE",
};

// ── Component ─────────────────────────────────────────────────────────
export function NeuralRibbon() {
  const [status, setStatus] = useState<StatusData>({
    status: "online",
    model: "—",
    tps: 0,
    vram: "—",
  });
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [expanded, setExpanded] = useState(false);
  const mounted = useRef(true);

  // Fetch system health
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/system/health");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (!mounted.current) return;

      // Map backend health response
      setStatus((prev) => ({
        ...prev,
        status: data.status === "healthy" ? "online" : "degraded",
      }));

      // Track individual services if available
      if (data.services) {
        setServices(data.services);
      }
    } catch {
      if (mounted.current) {
        setStatus((prev) => ({ ...prev, status: "offline" }));
      }
    }
  }, []);

  // Fetch active model info
  const fetchModel = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/models/ollama/catalog");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (!mounted.current) return;

      const active = data.models?.find?.((m: Record<string, unknown>) => m.active);
      if (active) {
        setStatus((prev) => ({
          ...prev,
          model: String(active.name ?? "—"),
          tps: Number(active.tps ?? 0),
          vram: String(active.vram_used ?? "—"),
        }));
      }
    } catch {
      // Model info is non-critical — keep defaults
    }
  }, []);

  // Fetch on mount and poll every 30s
  useEffect(() => {
    mounted.current = true;
    fetchStatus();
    fetchModel();

    const interval = setInterval(() => {
      fetchStatus();
    }, 30000);

    return () => {
      mounted.current = false;
      clearInterval(interval);
    };
  }, [fetchStatus, fetchModel]);

  // ── Render ──────────────────────────────────────────────────────────
  const isDegraded = status.status === "degraded";
  const isOffline = status.status === "offline";

  return (
    <div className="relative">
      {/* Ribbon bar — always visible */}
      <div
        className={cn(
          "fixed top-0 left-0 right-0 z-sticky",
          "flex h-6 items-center justify-center gap-2.5",
          "bg-bg-base/80 backdrop-blur-sm",
          "border-b border-border-subtle",
          "px-4",
          "select-none",
        )}
      >
        {/* Status dot + label */}
        <button
          onClick={() => setExpanded(!expanded)}
          className={cn(
            "flex items-center gap-1 text-[11px] font-mono font-medium tracking-wide",
            "motion-safe:transition-colors motion-safe:duration-150",
            isOffline && "text-danger",
            isDegraded && "text-warning",
            !isOffline && !isDegraded && "text-success",
          )}
          aria-label={`System status: ${STATUS_LABEL[status.status]}`}
        >
          <span className="text-xs">
            <span className={cn(
              "inline-block w-1.5 h-1.5 rounded-full mr-0.5 align-middle motion-safe:animate-pulse-dot",
              status.status === "online" && "bg-success",
              status.status === "degraded" && "bg-warning",
              status.status === "offline" && "bg-danger",
            )} />
          </span>
          <span>{STATUS_LABEL[status.status]}</span>
        </button>

        {/* Separator */}
        <span className="text-border-default text-[10px]">·</span>

        {/* Active model */}
        <span className="flex items-center gap-1 text-[11px] text-text-muted font-mono">
          <BrainIcon size={12} /> {status.model}
        </span>

        {/* TPS — only when data exists */}
        {status.tps > 0 && (
          <>
            <span className="text-border-default text-[10px]">·</span>
            <span className="text-[11px] text-text-muted font-mono">
              📡 {status.tps.toFixed(1)} t/s
            </span>
          </>
        )}

        {/* VRAM — only when data exists */}
        {status.vram !== "—" && (
          <>
            <span className="text-border-default text-[10px]">·</span>
            <span className="text-[11px] text-text-muted font-mono">
              💾 {status.vram}
            </span>
          </>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Version */}
        <span className="text-[10px] text-text-muted font-mono opacity-50">
          v1.0
        </span>
      </div>

      {/* Spacer to push content below ribbon */}
      <div className="h-6" />

      {/* Expanded health panel — dropdown */}
      {expanded && services.length > 0 && (
        <div
          className={cn(
            "fixed top-6 left-4 z-dropdown",
            "rounded-xl border border-border-default",
            "bg-bg-elevated p-3",
            "shadow-elevated",
            "min-w-[200px]",
            "animate-fade-in-scale",
          )}
        >
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">
            Services
          </p>
          <div className="space-y-1.5">
            {services.map((svc) => (
              <div
                key={svc.name}
                className="flex items-center justify-between gap-3"
              >
                <span className="text-xs text-text-primary font-mono">
                  {svc.name}
                </span>
                <span
                  className={cn(
                    "text-[10px] font-mono font-medium",
                    svc.status === "healthy" && "text-success",
                    svc.status === "degraded" && "text-warning",
                    svc.status === "down" && "text-danger",
                  )}
                >
                  {svc.status === "healthy" && "🟢"}
                  {svc.status === "degraded" && "🟡"}
                  {svc.status === "down" && "🔴"}
                  {" "}
                  {svc.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Offline overlay banner */}
      {isOffline && (
        <div className="fixed top-6 left-0 right-0 z-sticky bg-danger/10 border-b border-danger/20 px-4 py-1 text-center">
          <span className="text-[11px] text-danger font-mono">
            Backend unreachable — some features unavailable
          </span>
        </div>
      )}
    </div>
  );
}
