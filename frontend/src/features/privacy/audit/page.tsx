"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { audit, type AuditLog } from "../api";

const ACTIONS = ["all", "login", "logout", "create", "read", "update", "delete"] as const;
const PAGE_SIZE = 20;

function actionVariant(action: string): "success" | "default" | "warning" | "danger" {
  switch (action) {
    case "read":
    case "login":
      return "success";
    case "create":
      return "default";
    case "update":
    case "logout":
      return "warning";
    case "delete":
      return "danger";
    default:
      return "default";
  }
}

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffSec = Math.floor((now - then) / 1000);
  if (diffSec < 60) return "just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

function AuditLogItem({ log }: { log: AuditLog }) {
  const [expanded, setExpanded] = useState(false);
  const hasError = !!log.error_message;

  return (
    <div
      className="flex items-start gap-3 rounded-lg bg-bg-surface px-3 py-2.5 cursor-pointer hover:bg-bg-hover"
      onClick={() => hasError && setExpanded(!expanded)}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Badge variant={actionVariant(log.action)}>{log.action}</Badge>
          <span className={`text-xs ${log.success === 1 ? "text-success" : "text-danger"}`}>
            {log.success === 1 ? "Success" : "Failed"}
          </span>
        </div>
        <div className="mt-1 text-xs text-text-secondary">
          <span className="font-medium text-text-primary capitalize">{log.resource_type}</span>
          {log.resource_id && <span> / {log.resource_id}</span>}
        </div>
        {expanded && hasError && (
          <p className="mt-1.5 text-xs text-danger">{log.error_message}</p>
        )}
      </div>
      <div className="flex flex-col items-end gap-1 shrink-0">
        <span className="text-xs text-text-muted tabular-nums">{relativeTime(log.timestamp)}</span>
        {log.ip_address && (
          <span className="text-xs text-text-muted font-mono">{log.ip_address}</span>
        )}
      </div>
    </div>
  );
}

export default function AuditPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => { if (!loading && !user) router.push("/auth"); }, [user, loading, router]);

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [actionFilter, setActionFilter] = useState("all");
  const [userFilter, setUserFilter] = useState("");
  const [fetching, setFetching] = useState(false);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [hasMore, setHasMore] = useState(true);

  const loadLogs = async (effectiveLimit: number) => {
    setFetching(true);
    try {
      const params: { limit: number; action?: string } = {
        limit: effectiveLimit,
      };
      if (actionFilter !== "all") params.action = actionFilter;

      const res = await audit.logs(params);
      setLogs(res);
      setHasMore(res.length >= effectiveLimit);
    } catch {
      // silently fail — keep current data
    } finally {
      setFetching(false);
    }
  };

  // Refetch when filters change (reset pagination)
  useEffect(() => {
    setLimit(PAGE_SIZE);
    setLogs([]);
    setHasMore(true);
    loadLogs(PAGE_SIZE);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actionFilter, userFilter]);

  const handleLoadMore = () => {
    const newLimit = limit + PAGE_SIZE;
    setLimit(newLimit);
    loadLogs(newLimit);
  };

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-4xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Audit Log</h1>
          <p className="text-sm text-text-secondary mt-1">
            View security and activity audit logs
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="rounded-lg bg-bg-surface border border-border-subtle px-3 py-1.5 text-xs text-text-primary capitalize outline-none focus:border-accent/50"
          >
            {ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a === "all" ? "All actions" : a}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="User ID..."
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="rounded-lg bg-bg-surface border border-border-subtle px-3 py-1.5 text-xs text-text-primary w-28 outline-none focus:border-accent/50"
          />
        </div>

        {/* Log list */}
        {logs.length === 0 && !fetching ? (
          <EmptyState title="No audit logs found" />
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <AuditLogItem key={log.id} log={log} />
            ))}
          </div>
        )}

        {/* Load More */}
        {hasMore && logs.length > 0 && (
          <div className="flex justify-center pt-1">
            <Button
              variant="ghost"
              size="sm"
              loading={fetching}
              onClick={handleLoadMore}
            >
              Load More
            </Button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
