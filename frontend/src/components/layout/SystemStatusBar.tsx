"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "@/services/api/client";
import { Cpu, Database, RefreshCw, Terminal, CheckCircle2, AlertTriangle } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/state/store";
import { setIntelligence } from "@/state/slices/sync";
import { toggleCommandPalette } from "@/state/slices/ui";

interface HardwareStats {
  os: string;
  cpu: string;
  ram: {
    total_gb: number;
    available_gb: number;
    usage_percent: number;
  };
  gpu: {
    detected: boolean;
    name: string;
    total_vram_gb: number;
    free_vram_gb: number;
    utilization: number;
  };
}

export function SystemStatusBar() {
  const dispatch = useDispatch();
  const [hardware, setHardware] = useState<HardwareStats | null>(null);
  const [status, setStatus] = useState<"healthy" | "degraded" | "loading">("loading");
  const [routingProfile, setRoutingProfile] = useState<string>("Balanced");
  
  const intelligence = useSelector((state: RootState) => state.sync.intelligence);

  const fetchStats = async () => {
    try {
      // Fetch hardware
      const hardwareRes = await apiClient.get<HardwareStats>("/models/hardware");
      setHardware(hardwareRes.data);
      
      // Fetch deep health
      const healthRes = await apiClient.get<{ status: string }>("/health/deep");
      setStatus(healthRes.data.status === "healthy" ? "healthy" : "degraded");

      // Fetch intelligence status if not loaded
      if (!intelligence) {
        const intelRes = await apiClient.get("/workspace/intelligence");
        dispatch(setIntelligence(intelRes.data));
      }

      // Fetch active routing profile
      const routeRes = await apiClient.get("/models/routing/routes");
      setRoutingProfile(routeRes.data.profile_name || "Balanced");
    } catch (err) {
      console.error("Telemetry failed to fetch:", err);
      setStatus("degraded");
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 12000);
    return () => clearInterval(interval);
  }, []);

  const ramPercent = hardware?.ram?.usage_percent || 0;
  const vramPercent = hardware?.gpu?.detected 
    ? Math.round(((hardware.gpu.total_vram_gb - hardware.gpu.free_vram_gb) / hardware.gpu.total_vram_gb) * 100)
    : 0;

  return (
    <header className="h-11 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/60 px-4 flex items-center justify-between text-[11px] font-mono select-none tracking-wide text-slate-400">
      {/* Left Section: Live OS Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              status === "healthy" ? "bg-emerald-400" : status === "loading" ? "bg-amber-400" : "bg-rose-400"
            }`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              status === "healthy" ? "bg-emerald-500" : status === "loading" ? "bg-amber-500" : "bg-rose-500"
            }`}></span>
          </span>
          <span className="text-slate-200 font-semibold tracking-wider">CORTEX_OS</span>
        </div>

        <div className="hidden md:flex items-center gap-1 border-l border-slate-800 pl-4">
          <Terminal size={12} className="text-cyan-400" />
          <span>ROUTING:</span>
          <span className="text-cyan-400 font-semibold">{routingProfile.toUpperCase()}</span>
        </div>

        {intelligence && (
          <div className="hidden lg:flex items-center gap-1 border-l border-slate-800 pl-4">
            <Database size={12} className="text-emerald-400" />
            <span>KNOWLEDGE INDEXED:</span>
            <span className="text-slate-200 font-semibold">
              {intelligence.indexed_files}/{intelligence.total_files} FILES
            </span>
          </div>
        )}
      </div>

      {/* Right Section: Telemetry & Triggers */}
      <div className="flex items-center gap-6">
        {/* RAM Telemetry */}
        <div className="flex items-center gap-2">
          <span>RAM</span>
          <div className="w-16 h-1.5 bg-slate-900 rounded-sm overflow-hidden border border-slate-800">
            <div 
              className={`h-full transition-all duration-500 ${
                ramPercent > 85 ? "bg-rose-500" : ramPercent > 60 ? "bg-amber-500" : "bg-cyan-500"
              }`}
              style={{ width: `${ramPercent || 10}%` }}
            ></div>
          </div>
          <span className="text-slate-300 font-medium">{ramPercent}%</span>
        </div>

        {/* VRAM Telemetry */}
        {hardware?.gpu?.detected && (
          <div className="hidden sm:flex items-center gap-2">
            <span>VRAM</span>
            <div className="w-16 h-1.5 bg-slate-900 rounded-sm overflow-hidden border border-slate-800">
              <div 
                className={`h-full transition-all duration-500 ${
                  vramPercent > 85 ? "bg-rose-500" : vramPercent > 60 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${vramPercent || 10}%` }}
              ></div>
            </div>
            <span className="text-slate-300 font-medium">{vramPercent}%</span>
          </div>
        )}

        {/* Quick Command Trigger */}
        <button 
          onClick={() => dispatch(toggleCommandPalette())}
          className="flex items-center gap-1 px-2 py-0.5 rounded border border-slate-800 hover:border-slate-700 bg-slate-900/60 hover:bg-slate-900 text-slate-300 transition-colors shadow-inner"
        >
          <span>CMD</span>
          <span className="opacity-40 font-sans">+</span>
          <span>K</span>
        </button>
      </div>
    </header>
  );
}
