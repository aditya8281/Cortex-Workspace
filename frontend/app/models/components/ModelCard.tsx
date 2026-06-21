"use client";

import { useRouter } from "next/navigation";
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
  AlertTriangle,
} from "lucide-react";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ModelInfo, HardwareProfile } from "@/shared/types";

const modelTypeIcons: Record<string, typeof MessageSquare> = {
  chat: MessageSquare,
  code: Code,
  vision: Eye,
  embedding: FileText,
};

interface ModelCardProps {
  model: ModelInfo;
  hardware?: HardwareProfile | null;
  onDownload?: (modelName: string, variant?: string) => void;
  onCancel?: (modelName: string) => void;
  downloadProgress?: number | null;
  isDownloading?: boolean;
  onAddToCompare?: (modelId: string) => void;
  isInComparison?: boolean;
}

function formatSize(bytes?: number): string {
  if (!bytes) return "—";
  const gb = bytes / (1024 ** 3);
  return gb >= 1 ? `${gb.toFixed(1)}GB` : `${(bytes / (1024 ** 2)).toFixed(0)}MB`;
}

function isOversized(model: ModelInfo, hardware: HardwareProfile | null): boolean {
  if (!hardware || !model.hardware_requirements) return false;
  const vramNeeded = model.hardware_requirements.min_vram_gb;
  return hardware.gpu.available ? vramNeeded > hardware.gpu.vram_gb : vramNeeded > 0;
}

export default function ModelCard({
  model,
  hardware,
  onDownload,
  onCancel,
  downloadProgress,
  isDownloading,
  onAddToCompare,
  isInComparison,
}: ModelCardProps) {
  const router = useRouter();
  const [selectedVariant, setSelectedVariant] = useState<string | undefined>();
  const [showVariants, setShowVariants] = useState(false);

  const TypeIcon = modelTypeIcons[model.model_type] || MessageSquare;
  const installed = model.downloaded;
  const oversized = isOversized(model, hardware ?? null);
  const downloading = isDownloading || (downloadProgress != null && downloadProgress >= 0 && downloadProgress < 100);

  function handleCardClick() {
    router.push(`/models/${model.model_id || model.name}`);
  }

  function handleDownloadClick(e: React.MouseEvent) {
    e.stopPropagation();
    if (model.variants && model.variants.length > 0) {
      if (model.variants.length === 1) {
        onDownload?.(model.name, model.variants[0]);
      } else {
        onDownload?.(model.name, selectedVariant || model.variants[0]);
      }
    } else {
      onDownload?.(model.name);
    }
  }

  function handleCancelClick(e: React.MouseEvent) {
    e.stopPropagation();
    onCancel?.(model.name);
  }

  function handleCompareClick(e: React.MouseEvent) {
    e.stopPropagation();
    onAddToCompare?.(model.model_id);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Card
        hover={!downloading}
        className={cn(
          "group p-4 flex flex-col gap-3",
          installed && "border-success/20",
          oversized && "opacity-55",
          downloading && "cursor-default"
        )}
        onClick={handleCardClick}
      >
        {/* Header: Type icon + Name + Badge */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div
              className={cn(
                "flex items-center justify-center h-8 w-8 rounded-lg shrink-0",
                "bg-accent/10 text-accent"
              )}
            >
              <TypeIcon className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-medium text-text truncate">
                {model.display_name || model.name}
              </h3>
              <p className="text-[11px] text-text-muted truncate">{model.provider}</p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {installed && (
              <Badge variant="success">Installed</Badge>
            )}
            <Badge variant="default">{model.parameter_count}</Badge>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
          {model.description}
        </p>

        {/* Meta row */}
        <div className="flex items-center gap-3 text-[11px] text-text-muted">
          <span className="flex items-center gap-1">
            <HardDrive className="h-3 w-3" />
            {formatSize(model.size_bytes)}
          </span>
          <span className="flex items-center gap-1">
            <Cpu className="h-3 w-3" />
            {(model.context_length / 1000).toFixed(0)}K ctx
          </span>
          {model.hardware_requirements && (
            <span className="flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {model.hardware_requirements.min_vram_gb}GB min VRAM
            </span>
          )}
        </div>

        {/* Capabilities */}
        {model.capabilities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {model.capabilities.slice(0, 3).map((cap) => (
              <span
                key={cap}
                className="px-2 py-0.5 rounded-md bg-bg-hover text-[10px] text-text-muted"
              >
                {cap}
              </span>
            ))}
            {model.capabilities.length > 3 && (
              <span className="px-2 py-0.5 rounded-md bg-bg-hover text-[10px] text-text-muted">
                +{model.capabilities.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Variant Selector */}
        {model.variants && model.variants.length > 1 && !installed && (
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowVariants(!showVariants);
              }}
              className={cn(
                "flex items-center justify-between w-full px-3 py-2 rounded-lg",
                "bg-bg-surface border border-border-subtle text-xs text-text-secondary",
                "hover:border-accent/30 transition-colors duration-200"
              )}
            >
              <span className="font-mono">{selectedVariant || model.variants[0]}</span>
              <ChevronDown
                className={cn(
                  "h-3.5 w-3.5 transition-transform duration-200",
                  showVariants && "rotate-180"
                )}
              />
            </button>
            {showVariants && (
              <div className="absolute z-50 bottom-full mb-1 w-full bg-bg-elevated border border-border-subtle rounded-lg shadow-lg overflow-hidden">
                {model.variants.map((v) => (
                  <button
                    key={v}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedVariant(v);
                      setShowVariants(false);
                    }}
                    className={cn(
                      "w-full px-3 py-2 text-left text-xs font-mono",
                      "hover:bg-bg-hover transition-colors duration-150",
                      v === selectedVariant
                        ? "text-accent bg-accent/10"
                        : "text-text-secondary"
                    )}
                  >
                    {v}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Oversized Warning */}
        {oversized && !installed && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-warning/10 border border-warning/20">
            <AlertTriangle className="h-3.5 w-3.5 text-warning shrink-0" />
            <span className="text-[11px] text-warning">
              Exceeds available VRAM — may run slowly
            </span>
          </div>
        )}

        {/* Download Progress */}
        {downloading && downloadProgress != null && (
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 rounded-full bg-bg-hover overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-accent"
                initial={{ width: 0 }}
                animate={{ width: `${downloadProgress}%` }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </div>
            <span className="font-mono text-[11px] text-text-secondary shrink-0">
              {Math.round(downloadProgress)}%
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-auto pt-1">
          {downloading ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="flex-1"
                onClick={handleCancelClick}
              >
                <X className="h-3.5 w-3.5" />
                Cancel
              </Button>
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />
                Downloading
              </div>
            </>
          ) : installed ? (
            <Button
              variant="secondary"
              size="sm"
              className="flex-1"
              onClick={(e) => {
                e.stopPropagation();
                router.push(`/models/${model.model_id || model.name}`);
              }}
            >
              <CheckCircle className="h-3.5 w-3.5" />
              Open
            </Button>
          ) : oversized ? (
            <Button
              variant="danger"
              size="sm"
              className="flex-1"
              onClick={handleDownloadClick}
            >
              <Download className="h-3.5 w-3.5" />
              Download Anyway
            </Button>
          ) : (
            <>
              <Button
                variant="primary"
                size="sm"
                className="flex-1"
                onClick={handleDownloadClick}
              >
                <Download className="h-3.5 w-3.5" />
                Download
              </Button>
              {onAddToCompare && (
                <Button
                  variant={isInComparison ? "secondary" : "ghost"}
                  size="sm"
                  onClick={handleCompareClick}
                >
                  {isInComparison ? "Added" : "Compare"}
                </Button>
              )}
            </>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
