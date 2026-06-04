"use client";

import { useState, useEffect } from "react";
import { Button, Card, Spinner, Badge } from "@/components/ui/base";
import { syncService } from "@/services/api/sync";
import type { SyncRun, WorkspaceIntelligence } from "@/types/api";

export default function SyncPage() {
  const [intelligence, setIntelligence] = useState<WorkspaceIntelligence | null>(null);
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [intData, statusData] = await Promise.all([
          syncService.getIntelligence(),
          syncService.getStatus(),
        ]);
        setIntelligence(intData);
      } catch (error) {
        console.error("Failed to fetch sync data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleTriggerSync = async () => {
    try {
      setSyncing(true);
      const result = await syncService.triggerSync();
      setSyncRuns([result, ...syncRuns]);
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Workspace Sync</h1>
        <Button onClick={handleTriggerSync} loading={syncing}>
          {syncing ? "Syncing..." : "Run Sync Now"}
        </Button>
      </div>

      {/* Intelligence Summary */}
      {intelligence && (
        <Card>
          <h2 className="text-xl font-bold mb-4">Status</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-400 text-sm">Total Files</p>
              <p className="text-2xl font-bold">{intelligence.total_files}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Indexed Files</p>
              <p className="text-2xl font-bold">{intelligence.indexed_files}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Status</p>
              <Badge>{intelligence.status}</Badge>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Last Sync</p>
              <p className="text-sm">{intelligence.last_sync || "Never"}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Sync History */}
      <Card>
        <h2 className="text-xl font-bold mb-4">Recent Runs</h2>
        {syncRuns.length === 0 ? (
          <p className="text-gray-400">No sync runs yet</p>
        ) : (
          <div className="space-y-2">
            {syncRuns.map((run) => (
              <div key={run.id} className="flex items-center justify-between p-2 bg-background rounded">
                <div>
                  <p className="font-medium">Run #{run.id}</p>
                  <p className="text-sm text-gray-400">{run.file_count} files</p>
                </div>
                <Badge variant={run.status === "complete" ? "secondary" : "danger"}>
                  {run.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
