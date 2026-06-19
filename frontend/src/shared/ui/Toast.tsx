"use client";

import { Toaster, toast } from "sonner";

export function ToastProvider() {
  return (
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-subtle)",
          color: "var(--text-primary)",
          borderRadius: "16px",
          fontSize: "13px",
        },
      }}
    />
  );
}

export { toast };
