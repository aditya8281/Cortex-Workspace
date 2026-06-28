"use client";

import { useMemo } from "react";
import { cn } from "@/shared/lib/utils";
import type { ModelVariantEntry } from "../api";
import { formatBytes } from "../api";
import { Badge } from "@/shared/ui/Badge";

interface VariantPickerProps {
  variants: ModelVariantEntry[];
  selectedVariantId: string | null;
  onSelect: (variantId: string) => void;
  disabled?: boolean;
}

/**
 * VariantPicker — compact list for selecting model quantization variants.
 * Shows quantization label, size, quality score bar, and installed badge.
 */
export function VariantPicker({
  variants,
  selectedVariantId,
  onSelect,
  disabled,
}: VariantPickerProps) {
  // Sort installed first, then by size ascending
  const sorted = useMemo(
    () =>
      [...variants].sort((a, b) => {
        if (a.downloaded !== b.downloaded) return a.downloaded ? -1 : 1;
        return (a.size_bytes ?? 0) - (b.size_bytes ?? 0);
      }),
    [variants],
  );

  if (sorted.length === 0) return null;

  return (
    <div className="space-y-1.5" role="radiogroup" aria-label="Select variant">
      {sorted.map((v) => {
        const isSelected = selectedVariantId === v.variant_id;

        return (
          <button
            key={v.variant_id}
            type="button"
            onClick={() => onSelect(v.variant_id)}
            disabled={disabled}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-colors duration-150",
              isSelected
                ? "border-accent bg-accent/8 text-text-primary"
                : "border-border-subtle bg-transparent text-text-secondary hover:border-border-default hover:text-text-primary",
              disabled && "pointer-events-none opacity-50",
            )}
            role="radio"
            aria-checked={isSelected}
            aria-label={`${v.quantization} variant, ${formatBytes(v.size_bytes ?? 0)}`}
          >
            {/* Quantization label */}
            <span className="font-mono text-xs font-semibold min-w-[4rem]">
              {v.quantization}
            </span>

            {/* Size */}
            <span className="text-xs text-text-muted min-w-[4.5rem]">
              {v.size_bytes != null ? formatBytes(v.size_bytes) : "?"}
            </span>

            {/* Quality score bar */}
            {v.quality_score != null && (
              <div className="flex items-center gap-1.5 flex-1 min-w-0">
                <div className="flex-1 h-1 rounded-full bg-bg-surface overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full",
                      v.quality_score >= 0.8
                        ? "bg-success"
                        : v.quality_score >= 0.5
                          ? "bg-warning"
                          : "bg-danger",
                    )}
                    style={{ width: `${Math.round(v.quality_score * 100)}%` }}
                  />
                </div>
                <span className="text-[0.625rem] text-text-muted font-mono tabular-nums w-8 text-right">
                  {Math.round(v.quality_score * 100)}%
                </span>
              </div>
            )}

            {/* Fallback spacer when no quality score */}
            {v.quality_score == null && (
              <span className="flex-1" />
            )}

            {/* Installed badge */}
            {v.downloaded && <Badge variant="success">Installed</Badge>}
          </button>
        );
      })}
    </div>
  );
}
