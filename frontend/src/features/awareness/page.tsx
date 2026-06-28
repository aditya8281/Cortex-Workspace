"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { DeviceCard } from "./components/DeviceCard";
import { EnvironmentCard } from "./components/EnvironmentCard";
import { HealthCard } from "./components/HealthCard";
import { ProjectCard } from "./components/ProjectCard";

export default function AwarenessPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-5xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Awareness</h1>
          <p className="text-sm text-text-secondary mt-1">System awareness and repository management</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DeviceCard />
          <EnvironmentCard />
          <HealthCard />
          <ProjectCard />
        </div>
      </div>
    </AppShell>
  );
}
