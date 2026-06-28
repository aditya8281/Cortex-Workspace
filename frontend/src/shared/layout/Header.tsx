"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { StatusDot } from "@/shared/ui/StatusDot";
import { Dropdown } from "@/shared/ui/Dropdown";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-sticky flex h-14 items-center justify-between border-b border-border-subtle bg-void/80 px-6 backdrop-blur-sm">
      {/* Left: page title area — empty by default, pages override */}
      <div />

      {/* Right: user */}
      <div className="flex items-center gap-3">
        <StatusDot color="success" pulse />
        <Dropdown
          align="right"
          trigger={
            <div className="flex items-center gap-2 cursor-pointer rounded-md px-2 py-1.5 hover:bg-bg-hover transition-colors duration-150">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-bg-surface text-xs font-semibold text-text-primary">
                {user?.username?.[0]?.toUpperCase() || "U"}
              </div>
              <span className="text-sm text-text-secondary hidden sm:inline">
                {user?.username || "User"}
              </span>
            </div>
          }
          items={[
            { label: "Settings", onClick: () => window.location.href = "/settings" },
            { label: "Sign out", onClick: logout, destructive: true },
          ]}
        />
      </div>
    </header>
  );
}
