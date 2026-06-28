"use client";

import { type ReactNode, createContext, useContext, useState, useCallback } from "react";
import { cn } from "@/shared/lib/utils";

type ToastVariant = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, variant: ToastVariant = "info") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-6 right-6 z-toast flex flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-4 py-3 text-sm shadow-elevated animate-fade-in-scale",
              "origin-bottom-right",
              t.variant === "success" && "border-success/30 bg-bg-elevated text-success",
              t.variant === "error" && "border-danger/30 bg-bg-elevated text-danger",
              t.variant === "info" && "border-accent/30 bg-bg-elevated text-accent",
            )}
            role="alert"
          >
            {t.variant === "success" && <span className="text-base">✓</span>}
            {t.variant === "error" && <span className="text-base">✕</span>}
            {t.variant === "info" && <span className="text-base">i</span>}
            <span className="text-text-primary">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
