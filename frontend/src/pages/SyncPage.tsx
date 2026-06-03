import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  useSyncStatus,
  useLatestSyncRun,
  useTriggerSync,
} from "@/hooks/useIntelligence";
import { formatTimestamp } from "@/lib/utils";
import { RefreshCw, Square } from "lucide-react";

export function SyncPage() {
  const { data: status, refetch } = useSyncStatus();
  const { data: run, refetch: refetchRun } = useLatestSyncRun();
  const syncMutation = useTriggerSync();
  const [logs, setLogs] = useState<string[]>([]);

  const isRunning = run?.status === "running" || syncMutation.isPending;

  useEffect(() => {
    if (!isRunning) return;
    const id = window.setInterval(() => {
      void refetch();
      void refetchRun();
    }, 2500);
    return () => window.clearInterval(id);
  }, [isRunning, refetch, refetchRun]);

  useEffect(() => {
    if (run?.progress_message) {
      setLogs((prev) => {
        const next = [...prev, `${new Date().toLocaleTimeString()} — ${run.progress_message}`];
        return next.slice(-20);
      });
    }
    if (run?.result_summary) {
      setLogs((prev) => [...prev, `${new Date().toLocaleTimeString()} — ${run.result_summary}`].slice(-20));
    }
  }, [run?.progress_message, run?.result_summary]);

  const progress = isRunning ? 45 : run?.status === "completed" ? 100 : 0;

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Sync Center</h2>
            <p className="text-sm text-cortex-muted">See exactly what Cortex is learning about your machine.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => syncMutation.mutate()} disabled={isRunning}>
              <RefreshCw className={`h-4 w-4 ${isRunning ? "animate-spin" : ""}`} />
              Sync Now
            </Button>
            <Button variant="secondary" disabled={!isRunning}>
              <Square className="h-4 w-4" />
              Stop
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current status</CardTitle>
            <CardDescription>{run?.progress_message ?? status?.progress_message ?? "Idle"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={progress} label="Sync progress" />
            <div className="flex flex-wrap gap-2">
              <Badge>Last: {formatTimestamp(status?.last_sync_time)}</Badge>
              <Badge variant={isRunning ? "warn" : "success"}>{run?.status ?? status?.last_sync_status ?? "idle"}</Badge>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2">
          {[
            ["Files indexed", run?.files_indexed ?? status?.files_indexed ?? 0],
            ["Repositories", run?.repositories_indexed ?? status?.repositories_indexed ?? 0],
            ["Added", run?.files_added ?? 0],
            ["Modified", run?.files_modified ?? 0],
            ["Removed", run?.files_removed ?? 0],
            ["Memory updates", run?.memory_updates ?? status?.memory_updates ?? 0],
          ].map(([label, value]) => (
            <Card key={label as string}>
              <CardContent className="p-4">
                <p className="text-xs text-cortex-muted">{label}</p>
                <p className="text-2xl font-semibold tabular-nums">{value as number}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Live logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-48 overflow-y-auto rounded-lg bg-cortex-bg p-3 font-mono text-xs text-cortex-muted">
              {logs.length === 0 && <p>Waiting for sync activity…</p>}
              {logs.map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </CardContent>
        </Card>

        {status?.discovery_roots && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Discovery roots</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {status.discovery_roots.map((root) => (
                <Badge key={root}>{root}</Badge>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
