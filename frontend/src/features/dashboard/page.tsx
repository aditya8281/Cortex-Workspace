"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { SystemOverview } from "./components/SystemOverview";
import { MetricsRow } from "./components/MetricsRow";
import { QuickActions } from "./components/QuickActions";
import { RecentActivity } from "./components/RecentActivity";
import { dashboardApi, type ActivityItem } from "./api";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [activityError, setActivityError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadActivity = useCallback(() => {
    setActivityError(null);
    dashboardApi
      .getRecentActivity()
      .then((res) => setActivity(res.items))
      .catch(() => setActivityError("Failed to load recent activity"));
  }, []);

  useEffect(() => {
    loadActivity();
  }, [loadActivity]);

  if (loading || !user) return (
    <AppShell>
      <div className="space-y-6">
        <div className="space-y-1">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-16 w-full rounded-lg" />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-6 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
              </div>
            </Card>
          ))}
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-32" />
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-3">
              <Skeleton className="h-3 w-2/3" />
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );

  return (
    <AppShell>
      <div className="space-y-6 stagger-children animate-fade-in">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Welcome back, {user.username}
          </p>
        </div>

        <SystemOverview />
        <MetricsRow />
        <QuickActions />

        <div>
          <h2 className="text-title font-semibold text-text-primary mb-3">
            Recent Activity
          </h2>
          {activityError ? (
            <div className="rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger">
              {activityError}
              <button
                onClick={loadActivity}
                className="ml-2 text-xs font-medium text-danger underline hover:text-danger/80"
              >
                Retry
              </button>
            </div>
          ) : (
            <RecentActivity items={activity} />
          )}
        </div>
      </div>
    </AppShell>
  );
}
