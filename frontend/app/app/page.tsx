"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Lock, Brain, Shield, User, Server, Activity, Cpu, MemoryStick, HardDrive, Terminal } from "lucide-react";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiVaultStatus, apiListMemory, apiSystemMetrics, apiSystemLogs } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import PageTransition from "../../src/shared/ui/PageTransition";
import StaggerChildren from "../../src/shared/ui/StaggerChildren";
import Card from "../../src/shared/ui/Card";
import type { VaultStatus, SystemMetrics, SystemLog } from "../../src/shared/types";

import type { LucideIcon } from "lucide-react";

function MetricRing({ value, label, icon: Icon, unit = "%" }: { value: number; label: string; icon: LucideIcon; unit?: string }) {
  const circumference = 2 * Math.PI * 36;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <Card className="p-4 group">
      <div className="flex items-center justify-between mb-3">
        <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
          <Icon className="h-4 w-4 text-accent" />
        </div>
        <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">{label}</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="relative w-20 h-20 shrink-0">
          <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
            <motion.circle
              cx="40" cy="40" r="36" fill="none" stroke="#06b6d4" strokeWidth="4"
              strokeLinecap="round" strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-semibold text-text font-display">
              {Math.round(value)}<span className="text-xs text-text-muted">{unit}</span>
            </span>
          </div>
        </div>
        <div className="min-w-0">
          <p className="text-xs text-text-muted">Active</p>
          <p className="text-xs text-text-secondary mt-0.5 truncate">
            {label === "GPU" ? "NVIDIA" : "System"}
          </p>
        </div>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [vaultStatus, setVaultStatus] = useState<VaultStatus | null>(null);
  const [memoryCount, setMemoryCount] = useState(0);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    apiVaultStatus().then(setVaultStatus).catch(() => {});
    apiListMemory({ limit: 1 }).then((data) => setMemoryCount(data.total ?? 0)).catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!user) return;
    apiSystemMetrics().then(setMetrics).catch(() => {});
    apiSystemLogs(15).then((data) => setLogs(data.logs)).catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!user) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/system`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "metrics") {
          setMetrics(data);
        }
      } catch {}
    };

    ws.onerror = () => {};
    ws.onclose = () => {};

    return () => { ws.close(); wsRef.current = null; };
  }, [user]);

  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      apiSystemLogs(15).then((data) => setLogs(data.logs)).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, [user]);

  if (loading || !user) return null;

  const initials = (user.full_name || user.username || "?").charAt(0).toUpperCase();
  const memberSince = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : "—";

  return (
    <DashboardShell>
      <PageTransition className="max-w-5xl mx-auto space-y-8">
        {/* Hero Welcome */}
        <div className="flex items-center gap-5">
          <motion.div whileHover={{ scale: 1.05 }} className="relative h-16 w-16 rounded-full bg-accent flex items-center justify-center text-xl font-bold text-[#050508] overflow-hidden shrink-0 cursor-default">
            {user.profile_photo ? (
              <img src={`/api/v1/me/profile/photo/${user.id}`} alt="" className="h-full w-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
            ) : initials}
          </motion.div>
          <div>
            <h1 className="text-2xl font-semibold text-text font-display tracking-tight">
              Welcome back, {user.full_name?.split(" ")[0] || user.username}
            </h1>
            <p className="text-sm text-text-secondary mt-0.5 flex items-center gap-1.5">
              {user.role === "admin" ? (
                <span className="inline-flex items-center gap-1"><Shield className="h-3.5 w-3.5 text-accent" />Admin</span>
              ) : "Member"} · @{user.username}
            </p>
          </div>
        </div>

        {/* System Metrics */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">System Metrics</h2>
          <StaggerChildren className="grid grid-cols-2 sm:grid-cols-4 gap-4" staggerDelay={0.06}>
            <MetricRing value={metrics?.cpu_percent ?? 0} label="CPU" icon={Cpu} />
            <MetricRing value={metrics?.ram_percent ?? 0} label="RAM" icon={MemoryStick} />
            <MetricRing value={metrics?.disk_percent ?? 0} label="Disk" icon={HardDrive} />
            <Card className="p-4 group">
              <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                  <Activity className="h-4 w-4 text-accent" />
                </div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">GPU</span>
              </div>
              <p className="text-lg font-semibold text-text font-display truncate">{metrics?.gpu_name ?? "—"}</p>
              <p className="text-xs text-text-muted mt-1">{metrics?.gpu_type || "No GPU"}</p>
            </Card>
          </StaggerChildren>
        </div>

        {/* Quick Stats */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">Quick Stats</h2>
          <StaggerChildren className="grid grid-cols-2 sm:grid-cols-4 gap-4" staggerDelay={0.06}>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Lock className="h-4 w-4 text-accent" />
                <div>
                  <p className="text-lg font-semibold text-text font-display">{vaultStatus?.locked ? "Locked" : "Active"}</p>
                  <p className="text-xs text-text-muted">Vault</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Brain className="h-4 w-4 text-accent" />
                <div>
                  <p className="text-lg font-semibold text-text font-display">{memoryCount}</p>
                  <p className="text-xs text-text-muted">Memories</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <User className="h-4 w-4 text-accent" />
                <div>
                  <p className="text-lg font-semibold text-text font-display">{memberSince}</p>
                  <p className="text-xs text-text-muted">Member since</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Server className="h-4 w-4 text-accent" />
                <div>
                  <p className="text-lg font-semibold text-text font-display">Connected</p>
                  <p className="text-xs text-text-muted">Server</p>
                </div>
              </div>
            </Card>
          </StaggerChildren>
        </div>

        {/* Live System Logs */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">System Logs</h2>
          <Card className="p-4 overflow-hidden">
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="h-4 w-4 text-accent" />
              <span className="text-xs font-mono text-text-muted">Recent activity</span>
              <span className="ml-auto h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
            </div>
            <div className="h-48 overflow-y-auto font-mono text-xs space-y-1">
              {logs.length === 0 ? (
                <p className="text-text-muted">No logs yet...</p>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="flex gap-2 py-0.5 hover:bg-bg-hover rounded px-2 -mx-2">
                    <span className="text-text-muted shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    <span className={`shrink-0 ${log.level === "ERROR" ? "text-error" : log.level === "WARNING" ? "text-warning" : "text-text-secondary"}`}>{log.level}</span>
                    <span className="text-text-muted truncate">{log.message}</span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">Quick Actions</h2>
          <StaggerChildren className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" staggerDelay={0.06}>
            <Card hover className="p-5 cursor-pointer" onClick={() => router.push("/vault")}>
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0"><Lock className="h-5 w-5 text-accent" /></div>
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text">Vault</h3>
                  <p className="text-xs text-text-muted truncate">Manage encrypted files</p>
                </div>
              </div>
            </Card>
            <Card hover className="p-5 cursor-pointer" onClick={() => router.push("/memory")}>
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0"><Brain className="h-5 w-5 text-accent" /></div>
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text">Memory</h3>
                  <p className="text-xs text-text-muted truncate">AI knowledge base</p>
                </div>
              </div>
            </Card>
            <Card hover className="p-5 cursor-pointer" onClick={() => router.push("/profile")}>
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0"><User className="h-5 w-5 text-accent" /></div>
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text">Profile</h3>
                  <p className="text-xs text-text-muted truncate">Account settings</p>
                </div>
              </div>
            </Card>
            {user.role === "admin" && (
              <Card hover className="p-5 cursor-pointer" onClick={() => router.push("/admin")}>
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0"><Shield className="h-5 w-5 text-accent" /></div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium text-text">Admin</h3>
                    <p className="text-xs text-text-muted truncate">User management</p>
                  </div>
                </div>
              </Card>
            )}
          </StaggerChildren>
        </div>
      </PageTransition>
    </DashboardShell>
  );
}