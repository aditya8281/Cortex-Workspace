"use client";

import { AuthGuard } from "@/components/shared/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";
import { SystemStatusBar } from "@/components/layout/SystemStatusBar";
import { CommandPalette } from "@/components/shared/CommandPalette";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex h-screen bg-background text-white overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <SystemStatusBar />
          <main className="flex-1 overflow-auto bg-slate-950/20">{children}</main>
        </div>
        <CommandPalette />
      </div>
    </AuthGuard>
  );
}
