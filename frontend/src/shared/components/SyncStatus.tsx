"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Check, Loader2 } from "lucide-react";
import { api } from "@/shared/api/client";

interface SyncStatusData {
  watching: number;
  pending_changes: number;
  status: "idle" | "syncing";
}

export default function SyncStatus() {
  const [status, setStatus] = useState<SyncStatusData | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.get<SyncStatusData>("/api/v1/sync/status");
        setStatus(data);
      } catch {}
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  return (
    <div className="flex items-center gap-2 text-xs text-text-muted">
      {status.status === "syncing" ? (
        <Loader2 size={12} className="animate-spin text-accent" />
      ) : (
        <Check size={12} className="text-success" />
      )}
      <span>
        {status.status === "syncing"
          ? `Syncing ${status.pending_changes} files...`
          : `${status.watching} repos watched`}
      </span>
    </div>
  );
}
