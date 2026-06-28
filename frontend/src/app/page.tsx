"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-void">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-headline font-semibold text-text-primary">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Welcome back, {user.username}
          </p>
        </div>

        {/* System status */}
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <StatusDot color="success" pulse />
            <div>
              <p className="text-sm font-medium text-text-primary">System Online</p>
              <p className="text-xs text-text-muted">All services operational</p>
            </div>
          </div>
        </Card>

        {/* Quick actions placeholder — built in Phase 2 */}
        <Card className="p-5">
          <p className="text-sm text-text-muted">Quick actions coming in Phase 2</p>
        </Card>
      </div>
    </AppShell>
  );
}
