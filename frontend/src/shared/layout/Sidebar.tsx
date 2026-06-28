"use client";

import { type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/shared/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: "grid" },
  { name: "Chat", href: "/chat", icon: "message" },
  { name: "Agents", href: "/agents", icon: "cpu" },
  { name: "Models", href: "/models", icon: "download" },
  { name: "System", href: "/system", icon: "activity" },
  { name: "Settings", href: "/settings", icon: "settings" },
] as const;

const iconMap: Record<string, React.ReactNode> = {
  grid: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="1" y="1" width="6" height="6" rx="1.5" />
      <rect x="11" y="1" width="6" height="6" rx="1.5" />
      <rect x="1" y="11" width="6" height="6" rx="1.5" />
      <rect x="11" y="11" width="6" height="6" rx="1.5" />
    </svg>
  ),
  message: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 4a2 2 0 012-2h10a2 2 0 012 2v7a2 2 0 01-2 2H7l-3 2.5V13H4a2 2 0 01-2-2V4z" />
    </svg>
  ),
  cpu: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="4" y="4" width="10" height="10" rx="2" />
      <path d="M7 1v3M11 1v3M7 14v3M11 14v3M1 7h3M14 7h3M1 11h3M14 11h3" />
    </svg>
  ),
  download: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M9 2v10M5 8l4 4 4-4M3 14h12" />
    </svg>
  ),
  activity: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M1 9h3l2-5 3 10 2-5h6" />
    </svg>
  ),
  settings: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="9" cy="9" r="2.5" />
      <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.05 3.05l1.41 1.41M13.54 13.54l1.41 1.41M3.05 14.95l1.41-1.41M13.54 4.46l1.41-1.41" />
    </svg>
  ),
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col bg-bg-elevated border-r border-border-subtle">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-border-subtle">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/12 text-accent">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0L16 8L8 16L0 8L8 0Z" />
          </svg>
        </div>
        <span className="text-title font-semibold text-text-primary">CORTEX</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-3 space-y-0.5">
        {navigation.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200",
                isActive
                  ? "bg-accent/10 text-accent"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
              )}
            >
              <span className="flex-shrink-0">{iconMap[item.icon]}</span>
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border-subtle">
        <p className="text-xs text-text-muted font-mono">v1.0.0</p>
      </div>
    </div>
  );
}
