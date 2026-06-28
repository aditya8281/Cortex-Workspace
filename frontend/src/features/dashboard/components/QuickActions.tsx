"use client";

import Link from "next/link";
import { Card } from "@/shared/ui/Card";

const actions = [
  {
    name: "New Chat",
    href: "/chat",
    description: "Start a conversation",
    icon: (
      <svg width="16" height="16" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M2 4a2 2 0 012-2h10a2 2 0 012 2v7a2 2 0 01-2 2H7l-3 2.5V13H4a2 2 0 01-2-2V4z" />
      </svg>
    ),
  },
  {
    name: "View Agents",
    href: "/agents",
    description: "Manage autonomous agents",
    icon: (
      <svg width="16" height="16" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="4" y="4" width="10" height="10" rx="2" />
        <path d="M7 1v3M11 1v3M7 14v3M11 14v3M1 7h3M14 7h3M1 11h3M14 11h3" />
      </svg>
    ),
  },
  {
    name: "System Health",
    href: "/system",
    description: "Check system status",
    icon: (
      <svg width="16" height="16" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M1 9h3l2-5 3 10 2-5h6" />
      </svg>
    ),
  },
];

export function QuickActions() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {actions.map((action) => (
        <Link key={action.name} href={action.href} className="group">
          <Card className="p-4 group-hover:border-accent/30">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-bg-surface text-text-muted group-hover:text-accent group-hover:bg-accent/8 transition-all duration-200">
                {action.icon}
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary group-hover:text-accent transition-colors duration-150">{action.name}</p>
                <p className="text-xs text-text-muted">{action.description}</p>
              </div>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}
