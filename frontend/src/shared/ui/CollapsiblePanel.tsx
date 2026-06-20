"use client";

import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface CollapsiblePanelProps {
  defaultOpen?: boolean;
  minWidth?: number;
  collapsedWidth?: number;
  className?: string;
  header: ReactNode;
  children: ReactNode;
}

export function CollapsiblePanel({
  defaultOpen = true,
  minWidth = 240,
  collapsedWidth = 48,
  className,
  header,
  children,
}: CollapsiblePanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={cn("flex h-full", className)}>
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div
            initial={{ width: collapsedWidth, opacity: 0.5 }}
            animate={{ width: minWidth, opacity: 1 }}
            exit={{ width: collapsedWidth, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="flex flex-col border-r border-border-subtle bg-bg-surface/50 overflow-hidden"
          >
            <div className="flex items-center justify-between p-3 border-b border-border-subtle">
              {header}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-md hover:bg-bg-hover text-text-secondary hover:text-text transition-colors"
              >
                <PanelLeftClose size={16} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center justify-center w-12 h-full border-r border-border-subtle hover:bg-bg-hover text-text-secondary hover:text-text transition-colors"
        >
          <PanelLeftOpen size={16} />
        </button>
      )}
    </div>
  );
}
