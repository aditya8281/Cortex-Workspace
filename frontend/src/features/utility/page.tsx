"use client";

import { UtilityIcon } from "@/shared/ui/icons";

export default function UtilityPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <UtilityIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Utility</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon</p>
      </div>
    </div>
  );
}
