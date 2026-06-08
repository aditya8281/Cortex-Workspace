/**
 * Dashboard page — Protected route shown after authentication.
 * Displays DashboardShell with empty content area (to be built later).
 */
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import DashboardShell from "../../src/shared/layout/DashboardShell";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <DashboardShell>
      {/* Empty content area — to be built later */}
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <p className="text-sm text-text-muted font-mono">
          Workspace coming soon.
        </p>
      </div>
    </DashboardShell>
  );
}
