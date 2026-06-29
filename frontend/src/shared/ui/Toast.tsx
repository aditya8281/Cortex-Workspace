"use client";

import { type ReactNode, createContext, useContext, useState, useCallback, useRef } from "react";
import { cn } from "@/shared/lib/utils";

type ToastVariant = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
  closing: boolean;
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 0;

const TOAST_ICONS: Record<ToastVariant, ReactNode> = {
  success: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 8.5l3.5 3.5L13 4" />
    </svg>
  ),
  error: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="6" />
      <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" />
    </svg>
  ),
  info: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="6" />
      <path d="M8 7v4M8 5v.01" />
    </svg>
  ),
};

const DISMISS_ICON = (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
    <path d="M3.5 3.5l7 7M10.5 3.5l-7 7" />
  </svg>
);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const removeToast = useCallback((id: number) => {
    // Start exit animation
    setToasts((prev) => prev.map((t) => t.id === id ? { ...t, closing: true } : t));
    // Unmount after exit animation
    const timer = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      timersRef.current.delete(id);
    }, 200);
    timersRef.current.set(id, timer);
  }, []);

  const addToast = useCallback((message: string, variant: ToastVariant = "info") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, message, variant, closing: false }]);
    // Auto-dismiss after 4s
    const timer = setTimeout(() => removeToast(id), 4000);
    timersRef.current.set(id, timer);
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      {/* Toast stack */}
      <div className="fixed bottom-6 right-6 z-toast flex flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-3 rounded-lg border px-4 py-3 text-sm shadow-elevated",
              "bg-bg-elevated min-w-[280px] max-w-[420px]",
              t.closing ? "animate-slide-out-to-right" : "animate-slide-in-from-right",
              t.variant === "success" && "border-success/20",
              t.variant === "error" && "border-danger/20",
              t.variant === "info" && "border-accent/20",
            )}
            role="alert"
          >
            <span className={cn(
              "flex-shrink-0",
              t.variant === "success" && "text-success",
              t.variant === "error" && "text-danger",
              t.variant === "info" && "text-accent",
            )}>
              {TOAST_ICONS[t.variant]}
            </span>
            <span className="text-text-primary flex-1">{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              className="flex-shrink-0 p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors duration-100"
              aria-label="Dismiss"
            >
              {DISMISS_ICON}
            </button>
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
