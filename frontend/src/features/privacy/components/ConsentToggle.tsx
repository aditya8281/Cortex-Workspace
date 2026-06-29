"use client";

import { useState } from "react";
import { cn } from "@/shared/lib/utils";
import { consent } from "../api";

interface ConsentToggleProps {
  scope: string;
  initialGranted: boolean;
  onToggle: (scope: string, granted: boolean) => void;
}

export function ConsentToggle({ scope, initialGranted, onToggle }: ConsentToggleProps) {
  const [granted, setGranted] = useState(initialGranted);
  const [saving, setSaving] = useState(false);

  const handleToggle = async () => {
    const next = !granted;
    setGranted(next);
    setSaving(true);

    try {
      if (next) {
        await consent.grant({ consent_type: scope });
      } else {
        await consent.revoke({ consent_type: scope });
      }
      onToggle(scope, next);
    } catch {
      // Revert toggle state on failure
      setGranted(!next);
    } finally {
      setSaving(false);
    }
  };

  return (
    <button
      type="button"
      role="switch"
      aria-checked={granted}
      aria-label={`Toggle consent for ${scope}`}
      onClick={handleToggle}
      disabled={saving}
      className={cn(
        "relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full",
        "transition-colors duration-150 ease-out",
        "focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-40",
        granted ? "bg-accent" : "bg-bg-surface border border-border-default",
      )}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 rounded-full bg-white shadow-sm",
          "transition-transform duration-150 ease-out",
          granted ? "translate-x-[18px]" : "translate-x-[1px]",
        )}
      />
    </button>
  );
}
