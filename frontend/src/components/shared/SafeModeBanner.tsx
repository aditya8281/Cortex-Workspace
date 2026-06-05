"use client";

import { useEffect, useState } from "react";

export function SafeModeBanner() {
  const [safeMode, setSafeMode] = useState<boolean>(false);

  useEffect(() => {
    try {
      const v = typeof window !== "undefined" ? localStorage.getItem("cortex_safe_mode") : null;
      setSafeMode(v === "1");
    } catch (e) {
      setSafeMode(false);
    }
  }, []);

  const exit = () => {
    try {
      localStorage.removeItem("cortex_safe_mode");
      setSafeMode(false);
      window.location.reload();
    } catch (e) {
      console.error(e);
    }
  };

  if (!safeMode) return null;

  return (
    <div className="w-full bg-amber-900 text-amber-50 px-4 py-2 text-xs flex items-center justify-between">
      <div>
        Cortex is running in Safe Mode: non-essential modules are disabled to preserve stability.
      </div>
      <div>
        <button onClick={exit} className="px-3 py-1 bg-amber-700 rounded text-[11px]">Exit Safe Mode</button>
      </div>
    </div>
  );
}
