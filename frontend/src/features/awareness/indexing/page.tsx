"use client";

import { AppShell } from "@/shared/layout/AppShell";

export default function AwarenessIndexingPage() {
  return (
    <AppShell>
      <div>
        <h1 className="text-headline font-semibold text-text-primary">Indexing</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Code indexing status and history
        </p>
      </div>
    </AppShell>
  );
}
