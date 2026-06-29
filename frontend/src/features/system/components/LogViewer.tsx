"use client";

import { Card } from "@/shared/ui/Card";
export interface SystemLog {
  timestamp: string;
  level: string;
  message: string;
  module: string;
  [key: string]: any;
}

const levelColors: Record<string, string> = {
  ERROR: "text-danger",
  WARNING: "text-warning",
  INFO: "text-text-secondary",
  DEBUG: "text-text-muted",
};

export function LogViewer({ logs }: { logs: SystemLog[] }) {
  if (!logs || !logs.length) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-text-muted">No logs available</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="px-4 py-3 border-b border-border-subtle">
        <h3 className="text-sm font-medium text-text-primary">System Logs</h3>
      </div>
      <div className="max-h-96 overflow-y-auto font-mono text-xs">
        {logs.map((log, i) => (
          <div
            key={i}
            className="flex gap-3 px-4 py-2 border-b border-border-subtle last:border-0"
          >
            <span className="text-text-muted whitespace-nowrap">
              {formatTimestamp(log.timestamp)}
            </span>
            <span className={`w-16 flex-shrink-0 font-semibold ${levelColors[log.level] ?? "text-text-muted"}`}>
              {log.level}
            </span>
            <span className="text-text-muted w-24 flex-shrink-0 truncate">
              {log.module}
            </span>
            <span className="text-text-primary flex-1 min-w-0 break-all">
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-US", { hour12: false });
  } catch {
    return "";
  }
}
