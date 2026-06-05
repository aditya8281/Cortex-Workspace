"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, Loader, Badge } from "../../src/shared/ui";
import { getSessionToken } from "../../src/shared/auth/session";

const subtitles = [
  "I am the mind of the machine.",
  "Bootstrapping secure systems.",
  "Loading developer-grade intelligence.",
];

export default function BootPage() {
  const router = useRouter();

  useEffect(() => {
    if (getSessionToken()) {
      router.replace("/");
      return;
    }

    const redirectTimer = window.setTimeout(() => {
      router.replace("/landing");
    }, 800);

    return () => {
      window.clearTimeout(redirectTimer);
    };
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-cortex-bg px-cortex-16">
      <div className="w-full max-w-[640px] p-8 text-center">
        <h1 className="text-2xl font-medium text-cortex-text">Cortex Initialising</h1>
        <p className="mt-4 text-sm text-cortex-text-muted">Preparing application environment…</p>
      </div>
    </div>
  );
}
