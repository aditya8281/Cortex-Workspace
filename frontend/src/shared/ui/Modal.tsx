"use client";

import {
  type ReactNode,
  useEffect,
  useCallback,
  useRef,
  useState,
} from "react";
import { cn } from "@/shared/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, className }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const [mounted, setMounted] = useState(false);
  const [closing, setClosing] = useState(false);

  // Mount immediately when opened
  useEffect(() => {
    if (open) {
      setClosing(false);
      setMounted(true);
    }
  }, [open]);

  // Unmount after exit animation finishes
  const handleAnimationEnd = useCallback(() => {
    if (closing) {
      setMounted(false);
      setClosing(false);
    }
  }, [closing]);

  // Trigger close animation instead of instant unmount
  const handleClose = useCallback(() => {
    setClosing(true);
  }, []);

  // Start closing when open goes false
  useEffect(() => {
    if (!open && mounted && !closing) {
      setClosing(true);
    }
  }, [open, mounted, closing]);

  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    },
    [handleClose],
  );

  // Focus trap
  const handleTabTrap = useCallback(
    (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !panelRef.current) return;
      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [],
  );

  useEffect(() => {
    if (!mounted || closing) return;
    previousFocusRef.current = document.activeElement as HTMLElement;
    requestAnimationFrame(() => {
      panelRef.current?.focus();
    });
    document.addEventListener("keydown", handleEscape);
    document.addEventListener("keydown", handleTabTrap);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.removeEventListener("keydown", handleTabTrap);
      document.body.style.overflow = "";
      previousFocusRef.current?.focus();
    };
  }, [mounted, closing, handleEscape, handleTabTrap]);

  if (!mounted) return null;

  const backdropAnim = closing ? "animate-fade-out" : "animate-fade-in";
  const panelAnim = closing ? "animate-scale-out" : "animate-fade-in-scale";

  return (
    <div className="fixed inset-0 z-modal flex items-center justify-center">
      {/* Backdrop */}
      <div
        className={cn("absolute inset-0 bg-black/60", backdropAnim)}
        onClick={handleClose}
        aria-hidden="true"
      />
      {/* Panel */}
      <div
        ref={panelRef}
        tabIndex={-1}
        className={cn(
          "relative z-10 w-full max-w-lg mx-4 rounded-xl border border-border-default bg-bg-elevated shadow-modal",
          panelAnim,
        )}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === "string" ? title : undefined}
        onAnimationEnd={panelAnim === "animate-scale-out" ? handleAnimationEnd : undefined}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
            <h2 className="text-title font-semibold text-text-primary">{title}</h2>
            <button
              onClick={handleClose}
              className="rounded-md p-1.5 text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none"
              aria-label="Close"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          </div>
        )}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}
