"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { SystemOverview } from "./components/SystemOverview";
import { MetricsRow } from "./components/MetricsRow";
import { QuickActions } from "./components/QuickActions";
import { RecentActivity } from "./components/RecentActivity";
import { dashboardApi, type ActivityItem } from "./api";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activity, setActivity] = useState<ActivityItem[]>([]);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    dashboardApi
      .getRecentActivity()
      .then((res) => setActivity(res.items))
      .catch(() => {});
  }, []);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="space-y-6 stagger-children">
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
          <RecentActivity items={activity} />
        </div>
      </div>
    </AppShell>
  );
}
