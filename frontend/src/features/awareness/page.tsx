"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
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

  if (loading || !user) return (
      <div className="max-w-5xl space-y-6">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-4 w-56" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-5">
              <div className="space-y-3">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-3 w-40" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            </Card>
          ))}
        </div>
      </div>
  );

  return (
      <div className="max-w-5xl space-y-6 animate-fade-in">
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
  );
}
