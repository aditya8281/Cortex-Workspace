"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Download,
  CheckCircle,
  Loader2,
  X,
  Cpu,
  HardDrive,
  Zap,
  Eye,
  Code,
  MessageSquare,
  FileText,
  ChevronDown,
} from "lucide-react";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import Dropdown, { DropdownItem } from "@/shared/ui/Dropdown";
import type { ModelInfo, HardwareInfo } from "@/shared/types";

const modelTypeIcons: Record<string, typeof MessageSquare> = {
  chat: MessageSquare,
  code: Code,
  vision: Eye,
  embedding: FileText,
};

const capabilityBadgeVariant: Record<string, "accent" | "success" | "warning" | "default"> = {
  chat: "accent",
  code: "success",
  reasoning: "warning",
  vision: "accent",
  embedding: "default",
};

interface ModelCardProps {
  model: ModelInfo;
  hardware?: HardwareInfo | null;
  onDownload?: (modelName: string, variant?: string) => void;
  onCancel?: (modelName: string) => void;
  downloadProgress?: number | null;
  isDownloading?: boolean;
}

export default function ModelCard({
  model,
  hardware,
  onDownload,
  onCancel,
  downloadProgress,
  isDownloading = false,
}: ModelCardProps) {
  const TypeIcon = modelTypeIcons[model.model_type] || Cpu;
  const meetsRequirements = hardware && model.hardware_requirements
    ? hardware.ram_gb >= model.hardware_requirements.min_ram_gb
    : true;
  const isRecommended = model.recommended ?? false;
  const hasVariants = model.variants && model.variants.length > 0;

  const [selectedVariant, setSelectedVariant] = useState<string | null>(null);

  const progressPercent =
    downloadProgress !== null && downloadProgress !== undefined
      ? Math.round(downloadProgress * 100)
      : 0;

  const handleDownload = () => {
    if (hasVariants) {
      const variantToUse = selectedVariant || model.variants?.[0] || null;
      onDownload?.(model.name, variantToUse || undefined);
    } else {
      onDownload?.(model.name);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Card
        hover={!model.downloaded && !isDownloading}
        gradient
        className="p-5 h-full flex flex-col"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
              <TypeIcon size={18} className="text-accent" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-text truncate">
                {model.display_name}
              </h3>
              <p className="text-xs text-text-muted font-mono truncate">
                {model.name}
              </p>
            </div>
          </div>
          {isRecommended && (
            <Badge variant="accent">Recommended</Badge>
          )}
        </div>

        {/* Description */}
        <p className="text-xs text-text-secondary mb-3 line-clamp-2 flex-1">
          {model.description}
        </p>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-3 mb-3 text-xs text-text-muted">
          {model.parameter_count && (
            <span className="flex items-center gap-1">
              <Cpu size={12} />
              {model.parameter_count}
            </span>
          )}
          {model.hardware_requirements && (
            <span className="flex items-center gap-1">
              <HardDrive size={12} />
              {model.hardware_requirements.min_ram_gb}GB min
            </span>
          )}
          <span className="flex items-center gap-1">
            <Zap size={12} />
            {(model.context_length / 1000).toFixed(0)}K ctx
          </span>
        </div>

        {/* Capabilities */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {model.capabilities.map((cap) => (
            <Badge key={cap} variant={capabilityBadgeVariant[cap] ?? "default"}>
              {cap}
            </Badge>
          ))}
        </div>

        {/* Hardware warning */}
        {hardware && !meetsRequirements && model.hardware_requirements && (
          <div className="mb-3 px-3 py-2 rounded-lg bg-warning/10 border border-warning/20">
            <p className="text-xs text-warning">
              Requires {model.hardware_requirements.min_ram_gb}GB RAM. Your system has{" "}
              {hardware.ram_gb}GB.
            </p>
          </div>
        )}

        {/* Action */}
        <div className="mt-auto pt-2 border-t border-border-subtle">
          {model.downloaded ? (
            <div className="flex items-center gap-2 text-success">
              <CheckCircle size={16} />
              <span className="text-xs font-medium">Available</span>
            </div>
          ) : isDownloading ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 size={14} className="text-accent animate-spin" />
                  <span className="text-xs text-text-secondary">
                    Downloading {progressPercent}%
                  </span>
                </div>
                {onCancel && (
                  <button
                    onClick={() => onCancel(model.name)}
                    className="text-text-muted hover:text-danger transition-colors"
                    aria-label="Cancel download"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
              <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-accent"
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPercent}%` }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                />
              </div>
            </div>
          ) : hasVariants ? (
            <div className="flex items-center gap-2">
              <Dropdown
                trigger={
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={!meetsRequirements}
                    className="flex-1"
                  >
                    <Download size={14} />
                    Download ({selectedVariant?.toUpperCase() || model.variants?.[0].toUpperCase() || ""})
                    <ChevronDown size={12} className="ml-1" />
                  </Button>
                }
              >
                {model.variants?.map((variant) => (
                  <DropdownItem
                    key={variant}
                    onSelect={() => setSelectedVariant(variant)}
                    className={selectedVariant === variant ? "bg-accent/10 text-accent" : ""}
                  >
                    {variant.toUpperCase()}
                  </DropdownItem>
                ))}
              </Dropdown>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleDownload}
                disabled={!meetsRequirements}
              >
                <Download size={14} />
              </Button>
            </div>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownload}
              disabled={!meetsRequirements}
              className="w-full"
            >
              <Download size={14} />
              Download
            </Button>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
