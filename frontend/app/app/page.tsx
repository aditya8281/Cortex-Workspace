"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  Brain,
  Bot,
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  Server,
  Shield,
  User,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import Card from "@/shared/ui/Card";
import { MetricRing } from "@/shared/ui/MetricRing";
import { TabGroup, TabPanel } from "@/shared/ui/TabGroup";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import { useAuth } from "@/shared/auth/AuthProvider";
import { apiSystemMetrics, apiSystemLogs } from "@/shared/auth/cortexApi";
import { memoryApi } from "@/shared/api";
import { agentApi } from "@/shared/api";
import { useSystemWebSocket, type WebSocketStatus } from "@/shared/hooks/useSystemWebSocket";
import Link from "next/link";
import type { SystemMetrics, SystemLog } from "@/shared/types";
import SyncStatus from "@/shared/components/SyncStatus";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [recentActivity, setRecentActivity] = useState<SystemLog[]>([]);
  const [memoryCount, setMemoryCount] = useState<number | null>(null);
  const [agentCount, setAgentCount] = useState<number | null>(null);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>("disconnected");
  const httpFallbackRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const processes = metrics?.processes ?? [];

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  // ── WebSocket for live metrics + logs ──
  useSystemWebSocket({
    path: "/ws/system",
    enabled: !!user,
    onStatusChange: setWsStatus,
    onMessage(event) {
      try {
        const { type: _type, ...payload } = JSON.parse(event.data);
        if (_type === "metrics") {
          setMetrics((prev) => ({ ...prev, ...payload }));
        } else if (_type === "logs" && Array.isArray(payload.logs)) {
          setRecentActivity(payload.logs);
        }
      } catch {}
    },
  });

  // ── Cold-start HTTP fetch + fallback when WS is down ──
  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    // Cold-start: fetch immediately so UI isn't empty
    apiSystemMetrics()
      .then((data) => { if (!cancelled) setMetrics(data); })
      .catch(() => {});
    apiSystemLogs(15)
      .then((data) => { if (!cancelled) setRecentActivity(data.logs); })
      .catch(() => {});

    // Slow HTTP fallback when WebSocket is disconnected
    const startFallback = () => {
      if (httpFallbackRef.current) clearInterval(httpFallbackRef.current);
      httpFallbackRef.current = setInterval(() => {
        apiSystemMetrics()
          .then((data) => { if (!cancelled) setMetrics(data); })
          .catch(() => {});
        apiSystemLogs(15)
          .then((data) => { if (!cancelled) setRecentActivity(data.logs); })
          .catch(() => {});
      }, 30000);
    };

    const stopFallback = () => {
      if (httpFallbackRef.current) {
        clearInterval(httpFallbackRef.current);
        httpFallbackRef.current = null;
      }
    };

    // Watch wsStatus to toggle fallback
    if (wsStatus === "disconnected") {
      startFallback();
    } else {
      stopFallback();
    }

    return () => {
      cancelled = true;
      stopFallback();
    };
  }, [user, wsStatus]);

  useEffect(() => {
    if (!user) return;
    memoryApi.list({ limit: 1 }).then((data) => setMemoryCount(data.total ?? data.count ?? 0)).catch(() => {});
    agentApi.list().then((data) => {
      const agents = data.agents ?? data;
      setAgentCount(Array.isArray(agents) ? agents.length : 0);
    }).catch(() => {});
  }, [user]);

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <NeuralNetwork intensity="medium" />
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Hero Welcome */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-bg-surface border border-border-subtle flex items-center justify-center overflow-hidden">
                {user.profile_photo ? (
                  <img
                    src={`/api/v1/me/profile/photo/${user.id}`}
                    alt=""
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                ) : (
                  <User size={28} className="text-accent" />
                )}
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-success rounded-full border-2 border-bg" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-text">
                Welcome back, {user.full_name?.split(" ")[0] || user.username}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="micro-label">
                  {user.role === "admin" ? "Admin" : "Member"}
                </span>
                <span className="text-text-muted text-sm">@{user.username}</span>
              </div>
              <SyncStatus />
            </div>
          </div>

          {/* Premium Metric Rings */}
          <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12">
            <MetricRing label="CPU" value={metrics?.cpu_percent ?? 0} color="#0ea5c9" />
            <MetricRing label="RAM" value={metrics?.ram_percent ?? 0} color="#8b5cf6" />
            <MetricRing label="Disk" value={metrics?.disk_percent ?? 0} color="#22c55e" />
            <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4" gradient>
              <Cpu size={20} className="text-accent" />
              <span className="micro-label">GPU</span>
              <span className="text-sm text-text text-center">{metrics?.gpu_name ?? "N/A"}</span>
            </Card>
          </div>
        </motion.div>

        {/* Tabbed Content */}
        <TabGroup
          tabs={[
            { id: "activity", label: "Activity", icon: <Activity size={16} /> },
            { id: "processes", label: "Processes", icon: <Server size={16} />, count: processes.length },
            { id: "insights", label: "Insights", icon: <Brain size={16} /> },
          ]}
        >
          <TabPanel tabId="activity">
            <Card className="p-6" gradient>
              <h3 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Activity size={18} className="text-accent" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {recentActivity.length === 0 ? (
                  <p className="text-text-secondary text-sm">
                    No recent activity. Start by searching, creating agents, or adding memories.
                  </p>
                ) : (
                  recentActivity.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-bg-surface/50">
                      <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
                        <Bot size={14} className="text-accent" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-text truncate">{item.message}</p>
                        <p className="text-xs text-text-muted">{new Date(item.timestamp).toLocaleTimeString()}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </TabPanel>

          <TabPanel tabId="processes">
            <Card className="p-6" gradient>
              <h3 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Server size={18} className="text-accent" />
                System Processes
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-subtle">
                      <th className="text-left py-2 text-text-muted font-medium">Name</th>
                      <th className="text-right py-2 text-text-muted font-medium">PID</th>
                      <th className="text-right py-2 text-text-muted font-medium">CPU%</th>
                      <th className="text-right py-2 text-text-muted font-medium">Memory%</th>
                      <th className="text-right py-2 text-text-muted font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {processes.slice(0, 20).map((p: any, i: number) => (
                      <tr
                        key={i}
                        className="border-b border-border-subtle/50 hover:bg-bg-hover/50 transition-colors"
                      >
                        <td className="py-2 text-text font-mono text-xs">{p.name}</td>
                        <td className="py-2 text-text-secondary text-right font-mono text-xs">{p.pid}</td>
                        <td className="py-2 text-right font-mono text-xs">
                          <span className={p.cpu > 50 ? "text-warning" : "text-text-secondary"}>
                            {p.cpu?.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-2 text-right font-mono text-xs text-text-secondary">
                          {p.memory?.toFixed(1)}
                        </td>
                        <td className="py-2 text-right">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-xs ${
                              p.status === "running"
                                ? "bg-success/10 text-success"
                                : "bg-bg-hover text-text-muted"
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </TabPanel>

          <TabPanel tabId="insights">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Link href="/vault">
                <Card hover gradient className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                      <HardDrive size={18} className="text-accent" />
                    </div>
                    <span className="micro-label">Vault</span>
                  </div>
                  <p className="text-2xl font-semibold text-text">Active</p>
                </Card>
              </Link>
              <Link href="/memory">
                <Card hover gradient className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                      <Brain size={18} className="text-accent" />
                    </div>
                    <span className="micro-label">Memories</span>
                  </div>
                  <p className="text-2xl font-semibold text-text">{memoryCount ?? "—"}</p>
                </Card>
              </Link>
              <Card gradient className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                    <Bot size={18} className="text-accent" />
                  </div>
                  <span className="micro-label">Agents</span>
                </div>
                <p className="text-2xl font-semibold text-text">{agentCount ?? "—"}</p>
              </Card>
              <Card gradient className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                    <Clock size={18} className="text-accent" />
                  </div>
                  <span className="micro-label">Member Since</span>
                </div>
                <p className="text-sm font-semibold text-text">
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString()
                    : "—"}
                </p>
              </Card>
            </div>
          </TabPanel>
        </TabGroup>
      </div>
    </DashboardShell>
  );
}
