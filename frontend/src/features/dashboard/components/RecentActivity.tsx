"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { EmptyState } from "@/shared/ui/EmptyState";

const typeColors: Record<string, "default" | "success" | "warning" | "danger"> = {
  conversation: "default",
  agent: "success",
  system: "default",
  error: "danger",
};

interface ActivityItem {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
}

export function RecentActivity({ items }: { items: ActivityItem[] }) {
  if (!items || items.length === 0) {
    return (
      <Card className="p-6">
        <EmptyState
          title="No recent activity"
          description="Your recent conversations and agent runs will appear here"
        />
      </Card>
    );
  }

  return (
    <Card className="divide-y divide-border-subtle">
      {items.map((item, index) => (
        <div
          key={item.id}
          className="flex items-start gap-3 px-4 py-3"
          style={{ animationDelay: `${index * 40}ms` }}
        >
          <Badge variant={typeColors[item.type] ?? "default"}>
            {item.type}
          </Badge>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-text-primary truncate">{item.title}</p>
            <p className="text-xs text-text-muted truncate">{item.description}</p>
          </div>
          <span className="text-xs text-text-muted whitespace-nowrap">
            {formatTime(item.timestamp)}
          </span>
        </div>
      ))}
    </Card>
  );
}

function formatTime(timestamp: string): string {
  try {
    const diff = Date.now() - new Date(timestamp).getTime();
    if (diff < 60_000) return "just now";
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  } catch {
    return "";
  }
}
