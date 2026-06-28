"use client";

import { useState, useEffect, useCallback } from "react";
import type { ModelCatalogEntry } from "../api";
import { catalog, downloads, getDefaultModel, setDefaultModel, formatBytes, formatParamCount } from "../api";
import { Modal } from "@/shared/ui/Modal";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { cn } from "@/shared/lib/utils";
import { VariantPicker } from "./VariantPicker";

// ── Local types mirroring API responses ──────────────────────────────────

type ModelDetail = ModelCatalogEntry & {
  architecture?: string;
  license?: string;
  tags: string[];
  benchmarks?: Record<string, any>;
};

interface InferenceConfig {
  model_id: string;
  context_length?: number;
  temperature: number;
  top_p: number;
  top_k: number;
  repeat_penalty: number;
  seed: number;
  num_predict: number;
  num_ctx?: number;
  image_resolution?: number;
}

// ── Props ────────────────────────────────────────────────────────────────

interface ModelDetailModalProps {
  open: boolean;
  onClose: () => void;
  modelId: string;
  onDownload?: (modelName: string) => void;
  onSetDefault?: (modelId: string) => void;
}

// ── Inference config entry ───────────────────────────────────────────────

interface ConfigField {
  label: string;
  value: string | number;
}

function inferenceConfigFields(config: InferenceConfig): ConfigField[] {
  return [
    { label: "Temperature", value: config.temperature.toFixed(2) },
    { label: "Top-P", value: config.top_p.toFixed(2) },
    { label: "Top-K", value: config.top_k },
    { label: "Repeat Penalty", value: config.repeat_penalty.toFixed(2) },
    { label: "Num Predict", value: config.num_predict },
    { label: "Seed", value: config.seed },
    { label: "Context Length", value: config.num_ctx ?? config.context_length ?? "—" },
  ];
}

// ── Component ────────────────────────────────────────────────────────────

export function ModelDetailModal({
  open,
  onClose,
  modelId,
  onDownload,
  onSetDefault,
}: ModelDetailModalProps) {
  // Data state
  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [inferenceConfig, setInferenceConfig] = useState<InferenceConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Interaction state
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [defaultModelId, setDefaultModelId] = useState<string | null>(null);

  // Derived
  const defaultModel = defaultModelId;
  const isDefaultModel = detail ? detail.name === defaultModel : false;

  // Fetch data when modal opens
  const fetchData = useCallback(async () => {
    if (!modelId) return;
    setLoading(true);
    setError(null);

    try {
      const [detailData, configData] = await Promise.all([
        catalog.detail(modelId),
        catalog.inferenceConfig(modelId).catch(() => null),
      ]);
      setDetail(detailData as ModelDetail);
      setInferenceConfig(configData);

      // Auto-select first downloaded variant, or first variant
      if (detailData.variants.length > 0) {
        const downloaded = detailData.variants.find((v) => v.downloaded);
        setSelectedVariantId(downloaded?.variant_id ?? detailData.variants[0].variant_id);
      }
    } catch (e: any) {
      setError(e.message ?? "Failed to load model details");
    } finally {
      setLoading(false);
    }
  }, [modelId]);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (open) {
      setDefaultModelId(getDefaultModel());
      fetchData();
    } else {
      setDetail(null);
      setInferenceConfig(null);
      setSelectedVariantId(null);
      setDownloading(false);
      setError(null);
    }
  }, [open, fetchData]);

  // Handlers
  const handleVariantSelect = useCallback((variantId: string) => {
    setSelectedVariantId(variantId);
  }, []);

  const handleDownload = useCallback(async () => {
    if (!detail || !selectedVariantId) return;
    setDownloading(true);
    try {
      await downloads.download(detail.name, selectedVariantId);
      onDownload?.(detail.name);
      onClose();
    } catch (e: any) {
      setError(e.message ?? "Download failed");
    } finally {
      setDownloading(false);
    }
  }, [detail, selectedVariantId, onDownload, onClose]);

  const handleUseInChat = useCallback(() => {
    if (!detail) return;
    setDefaultModel(detail.name);
    setDefaultModelId(detail.name);
    onSetDefault?.(detail.name);
    onClose();
  }, [detail, onSetDefault, onClose]);

  // ── Loading state ────────────────────────────────────────────────────

  if (open && loading) {
    return (
      <Modal open={open} onClose={onClose} title="Loading..." className="max-w-xl">
        <div className="flex items-center justify-center py-12">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </div>
      </Modal>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────

  if (!loading && error) {
    return (
      <Modal open={open} onClose={onClose} title="Error" className="max-w-xl">
        <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      </Modal>
    );
  }

  // ── Main content ─────────────────────────────────────────────────────

  return (
    <Modal open={open} onClose={onClose} title={detail?.display_name ?? ""} className="max-w-xl">
      {detail && (
        <div className="space-y-5">
          {/* Provider + type */}
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <span className="font-medium">{detail.provider}</span>
            <span className="text-text-muted">·</span>
            <span className="capitalize">{detail.model_type}</span>
          </div>

          {/* Meta row: params, context, license */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-md bg-bg-surface px-2.5 py-1 font-mono text-xs text-text-primary">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-text-muted">
                <rect x="1" y="4" width="2" height="6" rx="0.5" fill="currentColor" />
                <rect x="4.5" y="1" width="2" height="9" rx="0.5" fill="currentColor" />
                <rect x="8" y="2.5" width="2" height="7.5" rx="0.5" fill="currentColor" />
              </svg>
              {formatParamCount(detail.parameter_count)}
            </span>

            {detail.context_length != null && (
              <span className="inline-flex items-center gap-1.5 rounded-md bg-bg-surface px-2.5 py-1 font-mono text-xs text-text-primary">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-text-muted">
                  <rect x="1" y="3" width="2" height="6" rx="0.5" fill="currentColor" />
                  <rect x="4.5" y="1" width="2" height="8" rx="0.5" fill="currentColor" />
                  <rect x="8" y="0" width="2" height="9" rx="0.5" fill="currentColor" />
                </svg>
                {(detail.context_length >= 1000
                  ? `${(detail.context_length / 1000).toFixed(0)}K`
                  : String(detail.context_length)
                )}{" "}
                ctx
              </span>
            )}

            {detail.license && (
              <Badge variant="default">{detail.license}</Badge>
            )}

            {/* Default model badge */}
            {isDefaultModel && <Badge variant="success">Default</Badge>}
          </div>

          {/* Capabilities */}
          {detail.capabilities.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {detail.capabilities.map((cap) => (
                <Badge key={cap} variant="default">
                  {cap}
                </Badge>
              ))}
            </div>
          )}

          {/* Description */}
          {detail.description && (
            <p className="text-sm text-text-secondary leading-relaxed">
              {detail.description}
            </p>
          )}

          {/* Architecture */}
          {detail.architecture && (
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <span className="font-medium text-text-secondary">Architecture:</span>
              <span className="font-mono">{detail.architecture}</span>
            </div>
          )}

          {/* Tags */}
          {detail.tags.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {detail.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center rounded-full bg-bg-surface px-2.5 py-0.5 font-mono text-[0.625rem] text-text-muted"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-border-subtle" />

          {/* Variants */}
          <div>
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              Variants
            </h4>
            {detail.variants.length > 0 ? (
              <VariantPicker
                variants={detail.variants}
                selectedVariantId={selectedVariantId}
                onSelect={handleVariantSelect}
                disabled={downloading}
              />
            ) : (
              <p className="text-xs text-text-muted">No variants available</p>
            )}
          </div>

          {/* Inference config */}
          {inferenceConfig && (
            <>
              <div className="border-t border-border-subtle" />
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                  Inference Config
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {inferenceConfigFields(inferenceConfig).map((field) => (
                    <div key={field.label} className="space-y-0.5">
                      <p className="text-[0.625rem] text-text-muted uppercase tracking-wider">
                        {field.label}
                      </p>
                      <p className="font-mono text-xs text-text-primary tabular-nums">
                        {field.value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Actions */}
          <div className="border-t border-border-subtle" />
          <div className="flex items-center gap-2 pt-1">
            <Button
              onClick={handleDownload}
              disabled={!selectedVariantId || downloading}
              loading={downloading}
            >
              {downloading
                ? "Downloading..."
                : selectedVariantId
                  ? `Download ${detail.variants.find((v) => v.variant_id === selectedVariantId)?.quantization ?? "Variant"}`
                  : "Download"}
            </Button>

            <Button
              variant="ghost"
              onClick={handleUseInChat}
              disabled={isDefaultModel}
            >
              {isDefaultModel ? "Default Model" : "Use in Chat"}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
