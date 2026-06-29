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
        if (!cancelled) setEntries(res);
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

  const handleToggle = useCallback((consentType: string, granted: boolean) => {
    setEntries((prev) =>
      prev.map((e) => (e.consent_type === consentType ? { ...e, granted: granted ? 1 : 0 } : e)),
    );
  }, []);

  const grantAll = async () => {
    setSavingAll(true);
    setEntries((prev) => prev.map((e) => ({ ...e, granted: 1 })));

    try {
      await Promise.all(entries.map((e) => consent.grant({ consent_type: e.consent_type })));
    } catch {
      const res = await consent.list();
      setEntries(res);
    } finally {
      setSavingAll(false);
    }
  };

  const revokeAll = async () => {
    setSavingAll(true);
    const grantedTypes = entries
      .filter((e) => e.granted)
      .map((e) => e.consent_type);

    setEntries((prev) => prev.map((e) => ({ ...e, granted: 0 })));

    try {
      await Promise.all(
        grantedTypes.map((ct) => consent.revoke({ consent_type: ct })),
      );
    } catch {
      const res = await consent.list();
      setEntries(res);
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
              <div key={entry.consent_type} className="flex items-center justify-between">
                <span className="text-xs text-text-secondary capitalize">
                  {entry.consent_type.replace(/_/g, " ")}
                </span>
                <ConsentToggle
                  scope={entry.consent_type}
                  initialGranted={entry.granted === 1}
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
