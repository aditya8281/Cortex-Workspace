"use client";

import { CodeIcon } from "@/shared/ui/icons";

export default function CodePage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <CodeIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Code</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon — v1.12</p>
      </div>
    </div>
  );
}
