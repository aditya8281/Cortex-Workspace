"use client";

import { useEffect, useState, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import { ConsentToggle } from "./ConsentToggle";
import { consent, type ConsentEntry } from "../api";

export function ConsentCard() {
  const [entries, setEntries] = useState<ConsentEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingAll, setSavingAll] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await consent.list();
        if (!cancelled) setEntries(res.items);
      } catch {
        // silently fail — component shows empty state
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const grantedCount = entries.filter((e) => e.granted).length;

  const handleToggle = useCallback((scope: string, granted: boolean) => {
    setEntries((prev) =>
      prev.map((e) => (e.scope === scope ? { ...e, granted } : e)),
    );
  }, []);

  const grantAll = async () => {
    setSavingAll(true);
    setEntries((prev) => prev.map((e) => ({ ...e, granted: true })));

    try {
      await Promise.all(entries.map((e) => consent.grant({ scope: e.scope })));
    } catch {
      // Revert on failure by refetching
      const res = await consent.list();
      setEntries(res.items);
    } finally {
      setSavingAll(false);
    }
  };

  const revokeAll = async () => {
    setSavingAll(true);
    const grantedScopes = entries
      .filter((e) => e.granted)
      .map((e) => e.scope);

    setEntries((prev) => prev.map((e) => ({ ...e, granted: false })));

    try {
      await Promise.all(
        grantedScopes.map((scope) => consent.revoke({ scope })),
      );
    } catch {
      // Revert on failure by refetching
      const res = await consent.list();
      setEntries(res.items);
    } finally {
      setSavingAll(false);
    }
  };

  const displayedEntries = entries.slice(0, 4);

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text-primary">Consent</h3>
        {!loading && (
          <span className="text-xs text-text-muted tabular-nums">
            {grantedCount}/{entries.length} granted
          </span>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-5 w-full" />
          <Skeleton className="h-5 w-full" />
        </div>
      ) : displayedEntries.length === 0 ? (
        <p className="text-xs text-text-muted">No consent entries</p>
      ) : (
        <>
          <div className="space-y-2.5 mb-4">
            {displayedEntries.map((entry) => (
              <div key={entry.id} className="flex items-center justify-between">
                <span className="text-xs text-text-secondary capitalize">
                  {entry.scope.replace(/_/g, " ")}
                </span>
                <ConsentToggle
                  scope={entry.scope}
                  initialGranted={entry.granted}
                  onToggle={handleToggle}
                />
              </div>
            ))}
          </div>

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
        </>
      )}
    </Card>
  );
}
