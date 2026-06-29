"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import { AccessControlCard } from "./components/AccessControlCard";
import { ConsentCard } from "./components/ConsentCard";
import { StorageCard } from "./components/StorageCard";
import { ExportCard } from "./components/ExportCard";

export default function PrivacyPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => { if (!loading && !user) router.push("/auth"); }, [user, loading, router]);
  if (loading || !user) return (
    <AppShell>
      <div className="max-w-5xl space-y-6">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-5">
              <div className="space-y-3">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
  return (
    <AppShell>
      <div className="max-w-5xl space-y-6 animate-fade-in">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Privacy & Trust</h1>
          <p className="text-sm text-text-secondary mt-1">Data privacy, access control, and consent management</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AccessControlCard />
          <ConsentCard />
          <StorageCard />
          <ExportCard />
        </div>
      </div>
    </AppShell>
  );
}
