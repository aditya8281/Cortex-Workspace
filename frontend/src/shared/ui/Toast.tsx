"use client";

import { Toaster, toast } from "sonner";

export function ToastProvider() {
  return (
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "#0a0a0f",
          border: "1px solid rgba(255,255,255,0.06)",
          color: "#f0f0f5",
          borderRadius: "12px",
          fontSize: "13px",
        },
      }}
    />
  );
}

export { toast };
