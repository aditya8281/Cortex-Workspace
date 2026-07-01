"use client";

import { BrainIcon } from "@/shared/ui/icons";

export default function BrainPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <BrainIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Brain</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon — v1.09</p>
      </div>
    </div>
  );
}
