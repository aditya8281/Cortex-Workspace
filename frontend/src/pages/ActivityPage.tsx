import { AnimatePresence, motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useLatestSyncRun,
  useProactiveNotifications,
  useWorkspaceIntelligence,
} from "@/hooks/useIntelligence";
import { getExecutionReplay } from "@/api/execution";
import { useChatStore } from "@/stores/chatStore";
import { formatTimestamp } from "@/lib/utils";

export function ActivityPage() {
  const { data: latest } = useLatestSyncRun();
  const { data: proactive = [] } = useProactiveNotifications();
  const { data: workspace } = useWorkspaceIntelligence();
  const activeSession = useChatStore((s) => s.getActiveSession());

  type JournalEntry = { time: string; title: string; detail: string; type: string };

  const latestExecutionId = [...(activeSession?.messages ?? [])]
    .reverse()
    .find((message) => message.sender === "assistant" && message.executionId)?.executionId ?? null;

  const { data: replay } = useQuery({
    queryKey: ["execution-replay", latestExecutionId],
    queryFn: () => getExecutionReplay(latestExecutionId as string),
    enabled: Boolean(latestExecutionId),
    refetchInterval: 10000,
  });

  const journal: JournalEntry[] = [
    ...(replay?.timeline?.map((event: any) => ({
      time: event.timestamp,
      title: event.human_readable || event.type,
      detail: event.payload?.tool
        ? `Tool: ${event.payload.tool}`
        : event.payload?.stage
          ? `${event.payload.stage}`
          : event.source || "Execution event",
      type: event.payload?.tool ? "tool" : "trace",
    })) ?? []),
    ...(latest?.completed_at
      ? [
          {
            time: latest.completed_at,
            title: "Sync completed",
            detail: latest.result_summary ?? "Environment sync finished",
            type: "sync",
          },
        ]
      : []),
    ...proactive.map((n) => ({
      time: n.created_at,
      title: n.title,
      detail: n.message,
      type: "observation",
    })),
    ...(workspace?.activity_feed.map((a) => ({
      time: new Date().toISOString(),
      title: a.title,
      detail: a.detail,
      type: a.tone,
    })) ?? []),
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h2 className="text-xl font-semibold">Activity Center</h2>
          <p className="text-sm text-cortex-muted">Cortex&apos;s internal journal of discoveries and changes.</p>
        </div>

        {latestExecutionId && (
          <Card className="border-cortex-accent/30 bg-cortex-accent-soft/20">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm">Live execution trace</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 text-sm text-cortex-muted">
              {replay ? (
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="accent">Execution {replay.execution_id}</Badge>
                    <Badge>{replay.status}</Badge>
                    <Badge variant="success">{replay.summary?.total_events ?? 0} events</Badge>
                  </div>
                  <p>{replay.summary?.summary ?? replay.summary?.status ?? "Tracing live tool usage."}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="h-3 w-28 rounded-full bg-cortex-border/70 animate-shimmer" />
                  <div className="h-3 w-3/4 rounded-full bg-cortex-border/50 animate-shimmer" />
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="space-y-3">
          <AnimatePresence initial={false}>
            {journal.map((item, i) => (
              <motion.div
                key={`${item.time}-${item.title}-${i}`}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
              >
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between gap-2 p-4 pb-2">
                    <CardTitle className="text-sm">{item.title}</CardTitle>
                    <Badge variant={item.type === "tool" ? "accent" : item.type === "sync" ? "success" : "default"}>{item.type}</Badge>
                  </CardHeader>
                  <CardContent className="p-4 pt-0 text-sm text-cortex-muted">
                    <p>{item.detail}</p>
                    <p className="mt-2 text-xs opacity-60">{formatTimestamp(item.time)}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
          {journal.length === 0 && (
            <p className="text-center text-sm text-cortex-muted">No activity yet. Run a sync to begin.</p>
          )}
        </div>
      </div>
    </div>
  );
}
