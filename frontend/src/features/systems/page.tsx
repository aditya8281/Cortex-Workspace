"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { SystemsIcon } from "@/shared/ui/icons";

export default function SystemsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <SystemsIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Systems</p>
        <p className="mt-1 text-sm text-text-muted">System overview & diagnostics</p>
      </div>
    </div>
  );
}
