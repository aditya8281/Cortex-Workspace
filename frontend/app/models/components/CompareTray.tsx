"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, GitCompareArrows } from "lucide-react";
import Button from "@/shared/ui/Button";

interface CompareTrayProps {
  selectedModels: string[];
  modelNames?: Record<string, string>;
  onRemove: (modelId: string) => void;
  onCompare: () => void;
  onClear: () => void;
}

const MAX_MODELS = 5;

export default function CompareTray({
  selectedModels,
  modelNames = {},
  onRemove,
  onCompare,
  onClear,
}: CompareTrayProps) {
  const canCompare = selectedModels.length >= 2;
  const atLimit = selectedModels.length >= MAX_MODELS;

  return (
    <AnimatePresence>
      {selectedModels.length > 0 && (
        <motion.div
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 80, opacity: 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 32 }}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-4"
        >
          <div
            className="flex items-center gap-3 rounded-2xl border border-border-subtle bg-bg-elevated/95 px-5 py-3 shadow-elevated backdrop-blur-xl"
          >
            <div className="flex items-center gap-2 text-text-secondary shrink-0">
              <GitCompareArrows className="h-4 w-4" />
              <span className="text-xs font-medium">
                {selectedModels.length}/{MAX_MODELS}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-1.5 min-w-0 flex-1">
              {selectedModels.map((id) => (
                <motion.span
                  key={id}
                  layout
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-bg-surface border border-border-subtle px-2.5 py-1 text-xs text-text"
                >
                  <span className="truncate max-w-[120px]">
                    {modelNames[id] || id}
                  </span>
                  <button
                    onClick={() => onRemove(id)}
                    className="shrink-0 rounded p-0.5 text-text-muted hover:text-text hover:bg-bg-hover transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </motion.span>
              ))}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button variant="ghost" size="sm" onClick={onClear}>
                Clear
              </Button>
              <Button
                variant="primary"
                size="sm"
                disabled={!canCompare}
                onClick={onCompare}
              >
                Compare Now
              </Button>
            </div>
          </div>

          {atLimit && (
            <p className="mt-1.5 text-center text-[11px] text-text-muted">
              Maximum {MAX_MODELS} models reached
            </p>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
