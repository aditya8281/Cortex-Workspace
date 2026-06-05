"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { Button } from "./button";

export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  size = "md",
}) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };

    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open || typeof document === "undefined") return null;

  const widths = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-cortex-bg/80 p-cortex-16 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={[
          "cortex-panel-motion w-full rounded-cortex-lg border border-cortex-border bg-cortex-bg-secondary p-cortex-24 text-cortex-text shadow-cortex-cyan",
          widths[size] || widths.md,
        ].join(" ")}
      >
        <div className="mb-cortex-16 flex items-start justify-between gap-cortex-16">
          <div>
            <h2 className="text-lg font-medium">{title}</h2>
          </div>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="text-sm text-cortex-text-muted">{children}</div>

        {footer ? <div className="mt-cortex-24 flex justify-end gap-cortex-12">{footer}</div> : null}
      </div>
    </div>,
    document.body
  );
}
