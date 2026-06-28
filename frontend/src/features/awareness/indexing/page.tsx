"use client";

import { useEffect } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { IndexingConfigForm } from "../components/IndexingConfigForm";

export default function IndexingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-3xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Indexing Configuration</h1>
          <p className="text-sm text-text-secondary mt-1">Configure how CORTEX indexes your files and repositories</p>
        </div>
        <IndexingConfigForm />
      </div>
    </AppShell>
  );
}
