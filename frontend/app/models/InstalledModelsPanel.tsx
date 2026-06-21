"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { CheckCircle, Play, Settings, Trash2, HardDrive } from "lucide-react";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import Skeleton from "@/shared/ui/Skeleton";
import { modelsApi } from "@/shared/api";
import type { ModelVariantInfo } from "@/shared/types";

export default function InstalledModelsPanel() {
  const [variants, setVariants] = useState<ModelVariantInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    modelsApi.installed()
      .then((data) => setVariants(data.models.flatMap(m => m.variants.filter(v => v.downloaded))))
      .catch((err) => console.error("Failed to load installed models:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (modelName: string) => {
    try {
      await modelsApi.delete(modelName);
      // Remove from local state
      setVariants(prev => prev.filter(v => v.variant_id !== modelName));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleRun = (modelName: string) => {
    // TODO: Implement model inference/selection
    console.log("Run model:", modelName);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-48" />
        ))}
      </div>
    );
  }

  if (variants.length === 0) {
    return (
      <Card className="p-8 text-center" gradient>
        <HardDrive size={40} className="text-text-muted mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-text mb-2">No models installed</h3>
        <p className="text-sm text-text-secondary max-w-md mx-auto">
          Browse the catalogue and download models to get started.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-text-secondary">
        {variants.length} model{variants.length !== 1 ? "s" : ""} installed
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {variants.map((variant, idx) => (
          <motion.div
            key={variant.variant_id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: idx * 0.05 }}
          >
            <Card className="p-4 h-full flex flex-col" gradient>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="text-sm font-semibold text-text">{variant.variant_id}</h4>
                  <p className="text-xs text-text-muted font-mono">
                    {variant.quantization} · {variant.size_gb?.toFixed(1)}GB
                  </p>
                </div>
                <Badge variant="success">
                  <CheckCircle size={12} className="mr-1" />
                  Installed
                </Badge>
              </div>

              <div className="flex flex-wrap gap-1.5 mb-3">
                <Badge variant="default" className="text-[10px]">
                  {variant.parameter_count}B
                </Badge>
                <Badge variant="default" className="text-[10px]">
                  Quality: {variant.quality_score?.toFixed(0)}%
                </Badge>
              </div>

              <div className="mt-auto pt-2 border-t border-border-subtle flex items-center gap-2">
                <Button variant="primary" size="sm" className="flex-1" onClick={() => handleRun(variant.variant_id)}>
                  <Play size={12} /> Run
                </Button>
                <Button variant="ghost" size="sm">
                  <Settings size={12} />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(variant.variant_id)}>
                  <Trash2 size={12} />
                </Button>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
