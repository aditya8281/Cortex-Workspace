import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useLatestSyncRun,
  useProactiveNotifications,
  useWorkspaceIntelligence,
} from "@/hooks/useIntelligence";
import { formatTimestamp } from "@/lib/utils";

export function ActivityPage() {
  const { data: latest } = useLatestSyncRun();
  const { data: proactive = [] } = useProactiveNotifications();
  const { data: workspace } = useWorkspaceIntelligence();

  type JournalEntry = { time: string; title: string; detail: string; type: string };

  const journal: JournalEntry[] = [
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

        <div className="space-y-3">
          {journal.map((item, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between gap-2 p-4 pb-2">
                <CardTitle className="text-sm">{item.title}</CardTitle>
                <Badge>{item.type}</Badge>
              </CardHeader>
              <CardContent className="p-4 pt-0 text-sm text-cortex-muted">
                <p>{item.detail}</p>
                <p className="mt-2 text-xs opacity-60">{formatTimestamp(item.time)}</p>
              </CardContent>
            </Card>
          ))}
          {journal.length === 0 && (
            <p className="text-center text-sm text-cortex-muted">No activity yet. Run a sync to begin.</p>
          )}
        </div>
      </div>
    </div>
  );
}
