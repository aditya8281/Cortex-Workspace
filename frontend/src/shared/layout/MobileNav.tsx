"use client";

import { type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/shared/lib/utils";

const tabs = [
  { name: "Home", href: "/", icon: "grid" },
  { name: "Chat", href: "/chat", icon: "message" },
  { name: "Agents", href: "/agents", icon: "cpu" },
  { name: "System", href: "/system", icon: "activity" },
  { name: "Settings", href: "/settings", icon: "settings" },
] as const;

const iconMap: Record<string, React.ReactNode> = {
  grid: (
    <svg width="20" height="20" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="1" y="1" width="6" height="6" rx="1.5" />
      <rect x="11" y="1" width="6" height="6" rx="1.5" />
      <rect x="1" y="11" width="6" height="6" rx="1.5" />
      <rect x="11" y="11" width="6" height="6" rx="1.5" />
    </svg>
  ),
  message: (
    <svg width="20" height="20" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 4a2 2 0 012-2h10a2 2 0 012 2v7a2 2 0 01-2 2H7l-3 2.5V13H4a2 2 0 01-2-2V4z" />
    </svg>
  ),
  cpu: (
    <svg width="20" height="20" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="4" y="4" width="10" height="10" rx="2" />
      <path d="M7 1v3M11 1v3M7 14v3M11 14v3M1 7h3M14 7h3M1 11h3M14 11h3" />
    </svg>
  ),
  activity: (
    <svg width="20" height="20" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M1 9h3l2-5 3 10 2-5h6" />
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="9" cy="9" r="2.5" />
      <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.05 3.05l1.41 1.41M13.54 13.54l1.41 1.41M3.05 14.95l1.41-1.41M13.54 4.46l1.41-1.41" />
    </svg>
  ),
};

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 inset-x-0 z-sticky flex lg:hidden items-center justify-around border-t border-border-subtle bg-bg-elevated px-2 py-1 safe-area-bottom">
      {tabs.map((tab) => {
        const isActive =
          tab.href === "/"
            ? pathname === "/"
            : pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.name}
            href={tab.href}
            className={cn(
              "flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[0.625rem] font-medium transition-colors duration-150",
              isActive
                ? "text-accent"
                : "text-text-muted",
            )}
          >
            <span className="flex-shrink-0">{iconMap[tab.icon]}</span>
            {tab.name}
          </Link>
        );
      })}
    </nav>
  );
}
