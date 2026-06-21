"use client";

import ModelCard from "./ModelCard";
import type { ModelInfo, HardwareProfile } from "@/shared/types";

interface CategorySectionProps {
  icon: React.ReactNode;
  title: string;
  count: number;
  models: ModelInfo[];
  hardware?: HardwareProfile | null;
  onDownload?: (modelName: string, variant?: string) => void;
  onCancel?: (modelName: string) => void;
  downloadProgress: Map<string, number>;
  downloadingModels: Set<string>;
}

export default function CategorySection({
  icon,
  title,
  count,
  models,
  hardware,
  onDownload,
  onCancel,
  downloadProgress,
  downloadingModels,
}: CategorySectionProps) {
  if (models.length === 0) return null;

  return (
    <section className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center h-7 w-7 rounded-lg bg-accent/10 text-accent">
            {icon}
          </div>
          <h2 className="text-sm font-medium text-text">{title}</h2>
          <span className="micro-label text-text-muted">{count}</span>
        </div>
        <button className="text-xs text-text-muted hover:text-accent transition-colors duration-200">
          See all →
        </button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {models.map((model) => (
          <ModelCard
            key={model.model_id}
            model={model}
            hardware={hardware}
            onDownload={onDownload}
            onCancel={onCancel}
            downloadProgress={downloadProgress.get(model.model_id) ?? null}
            isDownloading={downloadingModels.has(model.model_id)}
          />
        ))}
      </div>
    </section>
  );
}
