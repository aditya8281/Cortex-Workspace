import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  Brain,
  FolderGit2,
  Gauge,
  Layers,
  Network,
  RefreshCw,
  Search,
  Scan,
  MessageSquarePlus,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useSyncStatus,
  useLatestSyncRun,
  useProactiveNotifications,
  useAutomationSettings,
  useTriggerSync,
  useWorkspaceIntelligence,
} from "@/hooks/useIntelligence";
import { formatNumber, formatTimestamp } from "@/lib/utils";
import { useChatStore } from "@/stores/chatStore";
import { useAppStore } from "@/stores/appStore";
import { useQuery } from "@tanstack/react-query";
import { getMetricsSummary } from "@/api/ai";

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: status } = useSyncStatus();
  const { data: latest } = useLatestSyncRun();
  const { data: proactive = [] } = useProactiveNotifications();
  const { data: automation } = useAutomationSettings();
  const { data: workspace } = useWorkspaceIntelligence();
  const { data: metrics } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: getMetricsSummary,
    refetchInterval: 5000,
  });
  const syncMutation = useTriggerSync();
  const newSession = useChatStore((s) => s.newSession);
  const activeSession = useChatStore((s) => s.getActiveSession());
  const modelConfig = useAppStore((s) => s.modelConfig);
  const activeModel = activeSession?.selectedModel || modelConfig.llm_model;

  const stats = [
    { label: "Active model", value: activeModel || "Auto", icon: Layers, detail: activeSession?.title || "Current chat route" },
    {
      label: "Memory indexing",
      value: `${status?.memory_updates ?? 0}`,
      icon: Brain,
      detail: status?.sync_status === "syncing" ? `${status?.progress_percent ?? 0}% indexed` : "Idle learning layer",
    },
    {
      label: "Sync progress",
      value: `${status?.indexed ?? 0}/${status?.total_files ?? 0}`,
      icon: Network,
      detail: status?.current_path ? status.current_path.split("/").slice(-2).join("/") : "No active filesystem scan",
    },
    {
      label: "System latency",
      value: metrics ? `${formatNumber(metrics.avg_response_time_ms, 0, "0")} ms` : "—",
      icon: Gauge,
      detail: metrics ? `${formatNumber(metrics.avg_tokens_per_second, 0, "0")} tok/s avg` : "No telemetry yet",
    },
  ];

  const feed = [
    latest?.result_summary && {
      title: "Sync completed",
      detail: latest.result_summary,
      tone: "success" as const,
    },
    ...(workspace?.activity_feed.slice(0, 4).map((item) => ({
      title: item.title,
      detail: item.detail,
      tone: item.tone,
    })) ?? []),
    ...proactive.slice(0, 3).map((n) => ({
      title: n.title,
      detail: n.message,
      tone: "insight" as const,
    })),
  ].filter(Boolean) as { title: string; detail: string; tone: string }[];

  const quick = [
    { label: "Sync Now", icon: RefreshCw, action: () => syncMutation.mutate() },
    { label: "Analyze repository", icon: FolderGit2, action: () => navigate("/repositories") },
    { label: "Search files", icon: Search, action: () => navigate("/chat") },
    { label: "Open memory", icon: Brain, action: () => navigate("/memory") },
    { label: "Knowledge graph", icon: Network, action: () => navigate("/graph") },
    { label: "System scan", icon: Scan, action: () => navigate("/chat") },
    { label: "New chat", icon: MessageSquarePlus, action: () => { newSession(); navigate("/chat"); } },
  ];

  const isLoading = !status && !latest && workspace === undefined;

  return (
    <div className="h-full overflow-y-auto bg-cortex-bg p-4 md:p-6 lg:p-8">
      <div className="mx-auto max-w-5xl space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, ease: "easeOut" }}
          className="glass-panel relative overflow-hidden rounded-3xl border border-cortex-border/70 p-6 shadow-2xl shadow-black/20"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-cortex-accent/10 via-transparent to-cyan-500/10" />
          <div className="relative">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cortex-accent">Cortex OS</p>
                <h2 className="mt-2 text-3xl font-black tracking-tight text-cortex-text md:text-4xl">Your machine, understood</h2>
                <p className="mt-3 max-w-2xl text-sm text-cortex-muted">
                  Cortex continuously learns from your files, repositories, and workflows, then surfaces the right actions before you ask.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Badge variant="accent">Last sync: {formatTimestamp(status?.last_sync_time)}</Badge>
                <Badge>Automation: {automation?.automation_level ?? "approval"}</Badge>
                <Badge variant="accent">Model: {activeModel || "Auto"}</Badge>
                <Badge variant={latest?.status === "running" ? "warn" : "success"}>
                  {latest?.status === "running" ? "Syncing…" : status?.last_sync_status ?? "idle"}
                </Badge>
              </div>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {stats.map((s, index) => (
                <motion.div
                  key={s.label}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.24, ease: "easeOut", delay: index * 0.05 }}
                >
                  <Card className="h-full border-cortex-border/70 bg-cortex-surface/60">
                    <CardContent className="flex items-start gap-3 p-5">
                      <div className="rounded-xl bg-cortex-accent-soft p-2 text-cortex-accent shadow-sm shadow-cortex-accent/10">
                        <s.icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-2xl font-semibold tabular-nums text-cortex-text">{isLoading ? "—" : s.value}</p>
                        <p className="text-xs text-cortex-muted">{s.label}</p>
                        <p className="mt-1 text-[11px] text-cortex-muted/80 line-clamp-1">{s.detail}</p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-cortex-border/70 bg-cortex-surface/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cortex-accent shadow-[0_0_14px_rgba(109,156,255,0.8)]" />
                Cortex activity
              </CardTitle>
              <CardDescription>Recent learning and observations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <div className="space-y-3">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="glass-panel animate-shimmer rounded-2xl border border-cortex-border/60 p-4">
                      <div className="h-3 w-28 rounded-full bg-cortex-border/80" />
                      <div className="mt-3 h-3 w-full rounded-full bg-cortex-border/60" />
                      <div className="mt-2 h-3 w-4/5 rounded-full bg-cortex-border/50" />
                    </div>
                  ))}
                </div>
              ) : feed.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-cortex-border p-6 text-sm text-cortex-muted">
                  Run Sync Now to populate your activity feed.
                </div>
              ) : (
                <AnimatePresence initial={false}>
                  {feed.map((item, i) => (
                    <motion.div
                      key={`${item.title}-${i}`}
                      initial={{ opacity: 0, x: -12, y: 8 }}
                      animate={{ opacity: 1, x: 0, y: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      transition={{ duration: 0.2, ease: "easeOut", delay: i * 0.04 }}
                      className="rounded-2xl border border-cortex-border/70 bg-cortex-elevated/45 p-4 text-sm shadow-sm transition hover:-translate-y-0.5 hover:border-cortex-accent/30 hover:bg-cortex-elevated/65"
                    >
                      <p className="font-medium text-cortex-text">{item.title}</p>
                      <p className="mt-1 text-cortex-muted line-clamp-2">{item.detail}</p>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </CardContent>
          </Card>

          <Card className="border-cortex-border/70 bg-cortex-surface/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-cortex-success shadow-[0_0_14px_rgba(74,222,128,0.8)]" />
                Quick actions
              </CardTitle>
              <CardDescription>Common intelligence workflows</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2 sm:grid-cols-2">
              {quick.map((q, index) => (
                <motion.div
                  key={q.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, ease: "easeOut", delay: index * 0.035 }}
                >
                  <Button variant="secondary" className="justify-start" onClick={q.action}>
                    <q.icon className="h-4 w-4" />
                    {q.label}
                  </Button>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
