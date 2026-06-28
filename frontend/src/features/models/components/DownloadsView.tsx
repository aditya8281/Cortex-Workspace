"use client";

import { useState } from "react";
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
import { formatBytes, formatSpeed, formatEta } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DownloadsView() {
  const { state, actions } = useDownloadContext();
  const { active, queued, history } = state;
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleSelect = (jobId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(jobId)) next.delete(jobId);
      else next.add(jobId);
      return next;
    });
  };

  const handleBulkCancel = () => {
    actions.bulkCancel(Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  const totalItems = active.length + queued.length + history.length;

  if (totalItems === 0) {
    return (
      <EmptyState
        title="No downloads yet"
        description="Browse models to find one to download"
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Active downloads */}
      {active.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              Active ({active.length})
            </h3>
            {selectedIds.size > 0 && (
              <Button size="sm" variant="ghost" onClick={handleBulkCancel} className="text-danger">
                Cancel {selectedIds.size} selected
              </Button>
            )}
          </div>
          <div className="space-y-2">
            {active.map(job => {
              const percent = Math.round(job.progress * 100);
              return (
                <Card key={job.job_id} className="p-3">
                  <div className="flex items-center gap-3 mb-2">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(job.job_id)}
                      onChange={() => toggleSelect(job.job_id)}
                      className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface accent-accent"
                    />
                    <StatusDot color={job.status === "paused" ? "warning" : "accent"} pulse={job.status === "downloading"} />
                    <span className="text-sm text-text-primary font-mono flex-1 truncate">
                      {job.model_id}
                    </span>
                    <span className="text-xs text-text-muted font-mono">{percent}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-bg-surface overflow-hidden mb-2">
                    <div
                      className={`h-full rounded-full transition-[width] duration-300 ${
                        job.status === "paused" ? "bg-warning" : "bg-accent"
                      }`}
                      style={{ width: `${percent}%` }}
                      role="progressbar"
                      aria-valuenow={percent}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`Downloading ${job.model_id}: ${percent}%`}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">
                      {formatSpeed(job.speed_bytes_sec ?? 0)} · {formatEta(job.eta_seconds)}
                    </span>
                    <div className="flex items-center gap-1">
                      {job.status === "downloading" ? (
                        <Button size="sm" variant="ghost" onClick={() => actions.pause(job.job_id)}>
                          Pause
                        </Button>
                      ) : job.status === "paused" ? (
                        <Button size="sm" variant="ghost" onClick={() => actions.resume(job.job_id)}>
                          Resume
                        </Button>
                      ) : null}
                      <Button size="sm" variant="ghost" onClick={() => actions.cancel(job.model_id)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Queued */}
      {queued.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Queued ({queued.length})
          </h3>
          <div className="space-y-1">
            {queued.map(job => (
              <Card key={job.job_id} className="p-3 flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedIds.has(job.job_id)}
                  onChange={() => toggleSelect(job.job_id)}
                  className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface accent-accent"
                />
                <StatusDot color="warning" />
                <span className="text-sm text-text-primary font-mono flex-1 truncate">
                  {job.model_id}
                </span>
                <span className="text-xs text-text-muted">
                  Position: #{job.queue_position ?? "?"}
                </span>
                <Button size="sm" variant="ghost" onClick={() => actions.cancel(job.model_id)}>
                  Cancel
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              History ({history.length})
            </h3>
            <Button size="sm" variant="ghost" onClick={actions.clearCompleted}>
              Clear all
            </Button>
          </div>
          <div className="space-y-1">
            {history.map(item => (
              <div key={item.job_id} className="flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-bg-surface/50">
                <StatusDot
                  color={item.status === "completed" ? "success" : item.status === "failed" ? "danger" : "accent"}
                />
                <span className="text-text-primary font-mono flex-1 truncate">
                  {item.model_id}
                </span>
                <span className="text-xs text-text-muted">
                  {formatBytes(item.total_bytes)}
                </span>
                {item.status === "failed" && item.error && (
                  <span className="text-xs text-danger max-w-[200px] truncate">
                    {item.error}
                  </span>
                )}
                {item.status === "failed" && (
                  <Button size="sm" variant="ghost" onClick={() => actions.retry(item.model_id)}>
                    Retry
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
