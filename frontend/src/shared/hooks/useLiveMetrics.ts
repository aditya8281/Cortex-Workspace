"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { apiSystemMetrics } from "@/shared/auth/cortexApi";
import type { SystemMetrics } from "@/shared/types";

const POLL_INTERVAL_MS = 500;

/**
 * Shared hook that polls system metrics every 500ms.
 * Returns live CPU, RAM, GPU, disk, and process data.
 * Multiple components can use this — each gets the same live state.
 */
export function useLiveMetrics() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = useCallback(() => {
    apiSystemMetrics()
      .then((data) => setMetrics(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    // Cold-start fetch
    poll();

    // Poll every 500ms
    timerRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [poll]);

  return metrics;
}
