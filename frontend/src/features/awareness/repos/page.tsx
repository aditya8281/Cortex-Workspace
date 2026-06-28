"use client";

import { AppShell } from "@/shared/layout/AppShell";

export default function AwarenessReposPage() {
  return (
    <AppShell>
      <div>
        <h1 className="text-headline font-semibold text-text-primary">Repositories</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Monitored repositories and their awareness state
        </p>
      </div>
    </AppShell>
  );
}
