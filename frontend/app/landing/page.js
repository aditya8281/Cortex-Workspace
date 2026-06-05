"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    // nothing automatic; user can proceed to auth
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-cortex-bg px-cortex-16">
      <div className="w-full max-w-[640px] p-8 text-center">
        <h1 className="text-2xl font-medium text-cortex-text">Welcome to Cortex</h1>
        <p className="mt-4 text-sm text-cortex-text-muted">A minimalist landing page. Proceed to authentication.</p>
        <div className="mt-6">
          <button
            type="button"
            onClick={() => router.push('/auth')}
            className="rounded bg-cortex-cyan px-4 py-2 font-medium text-white"
          >
            Go to Login / Register
          </button>
        </div>
      </div>
    </div>
  );
}
