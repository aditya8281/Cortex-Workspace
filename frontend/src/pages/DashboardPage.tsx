import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain,
  FileStack,
  FolderGit2,
  GitBranch,
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
import { formatTimestamp } from "@/lib/utils";
import { useChatStore } from "@/stores/chatStore";

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: status } = useSyncStatus();
  const { data: latest } = useLatestSyncRun();
  const { data: proactive = [] } = useProactiveNotifications();
  const { data: automation } = useAutomationSettings();
  const { data: workspace } = useWorkspaceIntelligence();
  const syncMutation = useTriggerSync();
  const newSession = useChatStore((s) => s.newSession);

  const stats = [
    { label: "Repositories known", value: status?.repositories_indexed ?? 0, icon: GitBranch },
    { label: "Files indexed", value: status?.files_indexed ?? 0, icon: FileStack },
    { label: "Memory updates", value: status?.memory_updates ?? 0, icon: Brain },
    { label: "Graph nodes", value: (workspace?.concepts.length ?? 0) + (workspace?.repositories.length ?? 0), icon: Network },
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

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-5xl space-y-8"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-cortex-accent">Cortex OS</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">Your machine, understood</h2>
          <p className="mt-2 max-w-2xl text-sm text-cortex-muted">
            Cortex continuously learns from your files, repositories, and workflows — not just when you chat.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="accent">Last sync: {formatTimestamp(status?.last_sync_time)}</Badge>
            <Badge>Automation: {automation?.automation_level ?? "approval"}</Badge>
            <Badge variant={latest?.status === "running" ? "warn" : "success"}>
              {latest?.status === "running" ? "Syncing…" : status?.last_sync_status ?? "idle"}
            </Badge>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((s) => (
            <Card key={s.label}>
              <CardContent className="flex items-start gap-3 p-5">
                <div className="rounded-lg bg-cortex-accent-soft p-2 text-cortex-accent">
                  <s.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-semibold tabular-nums">{s.value}</p>
                  <p className="text-xs text-cortex-muted">{s.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Cortex activity</CardTitle>
              <CardDescription>Recent learning and observations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {feed.length === 0 && (
                <p className="text-sm text-cortex-muted">Run Sync Now to populate your activity feed.</p>
              )}
              {feed.map((item, i) => (
                <div key={i} className="rounded-lg border border-cortex-border bg-cortex-elevated/50 p-3 text-sm">
                  <p className="font-medium">{item.title}</p>
                  <p className="mt-1 text-cortex-muted line-clamp-2">{item.detail}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick actions</CardTitle>
              <CardDescription>Common intelligence workflows</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2 sm:grid-cols-2">
              {quick.map((q) => (
                <Button key={q.label} variant="secondary" className="justify-start" onClick={q.action}>
                  <q.icon className="h-4 w-4" />
                  {q.label}
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </div>
  );
}
