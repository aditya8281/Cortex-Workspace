"use client";

import { AuthGuard } from "@/components/shared/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard requireRole="admin">
      <div className="flex h-screen bg-background text-white">
        <Sidebar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </AuthGuard>
  );
}
