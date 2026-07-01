"use client";

import { VaultIcon } from "@/shared/ui/icons";

export default function VaultPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <VaultIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Vault</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon — v1.05</p>
      </div>
    </div>
  );
}
