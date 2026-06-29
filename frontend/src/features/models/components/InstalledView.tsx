"use client";

import { useState, useEffect } from "react";
import type { InstalledModel } from "../api";
import { downloads, setDefaultModel, getDefaultModel, formatBytes, formatParamCount } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";

interface InstalledViewProps {
  onViewDetail: (modelId: string) => void;
}

export function InstalledView({ onViewDetail }: InstalledViewProps) {
  const { actions } = useDownloadContext();
  const [models, setModels] = useState<InstalledModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [defaultModelId, setDefaultModelId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<InstalledModel | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await downloads.installed();
      setModels(res.models);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    setDefaultModelId(getDefaultModel());
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await downloads.syncInstalled();
      await load();
    } catch {
      // ignore
    } finally {
      setSyncing(false);
    }
  };

  const handleSetDefault = (modelId: string) => {
    setDefaultModel(modelId);
    setDefaultModelId(modelId);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await actions.deleteLocal(deleteTarget.model_id);
      setModels(prev => prev.filter(m => m.model_id !== deleteTarget.model_id));
      if (defaultModelId === deleteTarget.model_id) {
        setDefaultModelId(null);
        localStorage.removeItem("cortex_default_model");
      }
      setDeleteTarget(null);
    } catch (e: any) {
      setDeleteError(e.message ?? "Failed to delete model");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="p-4">
            <div className="space-y-3">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-3 w-1/3" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <EmptyState
        title="No models installed"
        description="Browse the catalog to download your first model"
      />
    );
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-secondary">
          {models.length} model{models.length !== 1 ? "s" : ""} installed
        </p>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleSync}
          disabled={syncing}
        >
          {syncing ? "Syncing..." : "Sync from Ollama"}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {models.map(model => {
          const isDefault = model.model_id === defaultModelId;
          const primaryVariant = model.variants?.[0];

          return (
            <Card key={model.model_id} className="p-4 flex flex-col gap-3" role="article" aria-label={model.display_name}>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-title font-semibold text-text-primary leading-tight">
                  {model.display_name}
                </h3>
                {isDefault && <Badge variant="success">Default</Badge>}
              </div>

              <p className="text-xs text-text-muted">
                {formatParamCount(model.parameter_count)} · {primaryVariant ? formatBytes(primaryVariant.size_bytes) : "?"} · {primaryVariant?.quantization ?? "?"}
              </p>

              <div className="flex items-center gap-1.5 flex-wrap">
                {model.capabilities?.map((cap) => (
                  <Badge key={cap} variant="default">{cap}</Badge>
                ))}
              </div>

              <div className="flex items-center gap-2 mt-auto pt-1">
                {!isDefault && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleSetDefault(model.model_id)}
                  >
                    Set as Default
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onViewDetail(model.model_id)}
                >
                  View Details
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="ml-auto text-danger hover:text-danger"
                  onClick={() => setDeleteTarget(model)}
                  aria-label={`Delete ${model.display_name}`}
                >
                  Delete
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Delete confirmation */}
      <Modal
        open={!!deleteTarget}
        onClose={() => { setDeleteTarget(null); setDeleteError(null); }}
        title="Delete Model"
      >
        <p className="text-sm text-text-secondary mb-4">
          Delete <span className="font-mono text-text-primary">{deleteTarget?.display_name}</span>? This will remove it from Ollama.
        </p>
        {deleteError && (
          <div className="mb-4 rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger">
            {deleteError}
          </div>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => { setDeleteTarget(null); setDeleteError(null); }}>
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            disabled={deleting}
            className="bg-danger hover:bg-danger/80"
          >
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </Modal>
    </>
  );
}
