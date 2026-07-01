"use client";

import { SearchIcon } from "@/shared/ui/icons";

export default function SearchPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <SearchIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Search</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon — v1.11</p>
      </div>
    </div>
  );
}
