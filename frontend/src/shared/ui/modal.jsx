"use client";

import React, { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

function getOrCreateModalRoot() {
  if (typeof document === "undefined") return null;
  let root = document.getElementById("cortex-modal-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "cortex-modal-root";
    document.body.appendChild(root);
  }
  return root;
}

export function Modal({ isOpen, onClose, title, children, className = "" }) {
  const root = getOrCreateModalRoot();
  const contentRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
      if (e.key === "Tab") {
        // simple focus trap
        const focusable = contentRef.current?.querySelectorAll(
          'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusable || focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    // focus first focusable
    setTimeout(() => {
      const focusable = contentRef.current?.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable && focusable.length) focusable[0].focus();
      else contentRef.current?.focus();
    }, 0);
  }, [isOpen]);

  if (!root) return null;
  if (!isOpen) return null;

  return createPortal(
    <div
      role="presentation"
      className="fixed inset-0 z-[900] flex items-center justify-center px-4 py-6"
      onMouseDown={(e) => {
        // close when clicking backdrop
        if (e.target === e.currentTarget) onClose?.();
      }}
    >
      <div className="absolute inset-0 bg-black/55 backdrop-blur-sm" aria-hidden="true" />

      <div
        ref={contentRef}
        role="dialog"
        aria-modal="true"
        aria-label={title || "Dialog"}
        tabIndex={-1}
        className={[
          "relative z-[901] w-full max-w-2xl rounded-[10px] border border-cortex-border bg-cortex-surface p-6",
          "shadow-[0_8px_40px_rgba(0,0,0,0.5)]",
          className,
        ].join(" ")}
      >
        {title && <h2 className="text-lg font-semibold text-cortex-text mb-2">{title}</h2>}
        <div>{children}</div>
        <button
          className="absolute right-3 top-3 text-cortex-text-muted hover:text-cortex-text"
          aria-label="Close dialog"
          onClick={() => onClose?.()}
        >
          ✕
        </button>
      </div>
    </div>,
    root
  );
}

export default Modal;
