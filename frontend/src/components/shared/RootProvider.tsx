"use client";

import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { useAuth } from "@/hooks/useAuth";
import { setUser } from "@/state/slices/auth";
import { SafeModeBanner } from "@/components/shared/SafeModeBanner";

export function RootProvider({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();
  const { checkAuth } = useAuth();
  useEffect(() => {
    // Check if user is already logged in on mount
    checkAuth();

    // Global error and rejection handlers to avoid uncaught crashes
    let rejectionCount = 0;
    const rejectionHandler = (ev: PromiseRejectionEvent) => {
      console.error("Unhandled promise rejection:", ev.reason);
      rejectionCount += 1;
      if (rejectionCount > 5) {
        try {
          localStorage.setItem("cortex_safe_mode", "1");
        } catch (e) {}
      }
    };

    const errorHandler = (ev: ErrorEvent) => {
      console.error("Global error:", ev.error || ev.message);
      rejectionCount += 1;
      if (rejectionCount > 5) {
        try {
          localStorage.setItem("cortex_safe_mode", "1");
        } catch (e) {}
      }
    };

    if (typeof window !== "undefined") {
      window.addEventListener("unhandledrejection", rejectionHandler as any);
      window.addEventListener("error", errorHandler as any);
    }

    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("unhandledrejection", rejectionHandler as any);
        window.removeEventListener("error", errorHandler as any);
      }
    };
  }, [checkAuth]);

  return (
    <>
      <SafeModeBanner />
      {children}
    </>
  );
}
