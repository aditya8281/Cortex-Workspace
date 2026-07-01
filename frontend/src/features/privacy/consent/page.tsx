"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { ConsentToggle } from "../components/ConsentToggle";
import { consent, type ConsentEntry } from "../api";
import { Skeleton } from "@/shared/ui/Skeleton";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ConsentPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => { if (!loading && !user) router.push("/auth"); }, [user, loading, router]);

  const [entries, setEntries] = useState<ConsentEntry[]>([]);
  const [fetching, setFetching] = useState(true);
  const [savingAll, setSavingAll] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await consent.list();
        if (!cancelled) setEntries(res);
      } catch {
        // silently fail — component shows empty state
      } finally {
        if (!cancelled) setFetching(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleToggle = useCallback((scope: string, granted: boolean) => {
    setEntries((prev) =>
      prev.map((e) => (e.consent_type === scope ? { ...e, granted: granted ? 1 : 0 } : e)),
    );
  }, []);

  const grantAll = async () => {
    setSavingAll(true);
    setEntries((prev) => prev.map((e) => ({ ...e, granted: 1 })));

    try {
      await Promise.all(entries.map((e) => consent.grant({ consent_type: e.consent_type })));
    } catch {
      // Revert on failure by refetching
      const res = await consent.list();
      setEntries(res);
    } finally {
      setSavingAll(false);
    }
  };

  const revokeAll = async () => {
    setSavingAll(true);
    const grantedScopes = entries.filter((e) => e.granted).map((e) => e.consent_type);
    setEntries((prev) => prev.map((e) => ({ ...e, granted: 0 })));

    try {
      await Promise.all(grantedScopes.map((consent_type) => consent.revoke({ consent_type })));
    } catch {
      // Revert on failure by refetching
      const res = await consent.list();
      setEntries(res);
    } finally {
      setSavingAll(false);
    }
  };

  if (loading || !user) return (
      <div className="max-w-4xl space-y-6">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-64" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Card key={i} className="p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1.5">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-48" />
                </div>
                <Skeleton className="h-6 w-10 rounded-full" />
              </div>
            </Card>
          ))}
        </div>
      </div>
  );

  const grantedCount = entries.filter((e) => e.granted).length;

  return (
      <div className="max-w-4xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Consent Management</h1>
          <p className="text-sm text-text-secondary mt-1">
            Control what data is collected and how it is used
          </p>
        </div>

        {entries.length > 0 && (
          <div className="flex items-center justify-between">
            <p className="text-xs text-text-muted tabular-nums">
              {grantedCount} of {entries.length} granted
            </p>
            <div className="flex gap-2">
              <Button
                variant="primary"
                size="sm"
                loading={savingAll}
                onClick={grantAll}
              >
                Grant All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                loading={savingAll}
                onClick={revokeAll}
              >
                Revoke All
              </Button>
            </div>
          </div>
        )}

        {entries.length === 0 && !fetching ? (
          <EmptyState title="No consent preferences configured" />
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <Card key={entry.consent_type}>
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-text-primary capitalize">
                      {entry.consent_type.replace(/_/g, " ")}
                    </p>
                    <p className="mt-0.5 text-xs text-text-muted">
                      {entry.consent_type}
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
                      <span>Granted: {formatDate(entry.created_at)}</span>
                      {entry.revoked_at && (
                        <span>Revoked: {formatDate(entry.revoked_at)}</span>
                      )}
                    </div>
                  </div>
                  <ConsentToggle
                    scope={entry.consent_type}
                    initialGranted={entry.granted === 1}
                    onToggle={handleToggle}
                  />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
  );
}
