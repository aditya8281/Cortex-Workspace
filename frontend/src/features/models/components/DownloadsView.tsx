"use client";

import { useState, useEffect, useRef } from "react";
import type { DownloadJob, DownloadHistoryItem } from "../api";
import { downloads } from "../api";
import { formatBytes, formatSpeed, formatEta } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DownloadsView() {
  const [active, setActive] = useState<DownloadJob[]>([]);
  const [queued, setQueued] = useState<DownloadJob[]>([]);
  const [completed, setCompleted] = useState<DownloadJob[]>([]);
  const [failed, setFailed] = useState<DownloadJob[]>([]);
  const [history, setHistory] = useState<DownloadHistoryItem[]>([]);
  const [showCompleted, setShowCompleted] = useState(false);
  const [showFailed, setShowFailed] = useState(true);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadQueue = async () => {
    try {
      const res = await downloads.queue();
      setActive(res.active);
      setQueued(res.queued);
      setCompleted(res.completed);
      setFailed(res.failed);
    } catch {
      // ignore
    }
  };

  const loadHistory = async () => {
    try {
      const res = await downloads.history(20);
      setHistory(res.history);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadQueue();
    loadHistory();
  }, []);

  // Poll while active downloads exist
  useEffect(() => {
    if (active.length > 0) {
      pollingRef.current = setInterval(() => {
        loadQueue();
      }, 2000);
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [active.length]);

  const handleCancel = async (modelName: string) => {
    try {
      await downloads.cancel(modelName);
      // Optimistic: move to failed
      setActive(prev => prev.filter(j => j.model_id !== modelName));
      setQueued(prev => prev.filter(j => j.model_id !== modelName));
      setFailed(prev => [
        ...prev,
        { job_id: `cancel-${Date.now()}`, model_id: modelName, status: "cancelled", progress: 0, speed_bytes_sec: null, downloaded_bytes: 0, total_bytes: 0, eta_seconds: null, queue_position: null, error: "Cancelled by user" },
      ]);
    } catch {
      // ignore
    }
  };

  const handleRetry = async (modelName: string) => {
    try {
      await downloads.download(modelName);
      setFailed(prev => prev.filter(j => j.model_id !== modelName));
      loadQueue();
    } catch {
      // ignore
    }
  };

  const totalItems = active.length + queued.length + completed.length + failed.length + history.length;

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
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Active ({active.length})
          </h3>
          <div className="space-y-2">
            {active.map(job => {
              const percent = Math.round(job.progress * 100);
              return (
                <Card key={job.job_id} className="p-3">
                  <div className="flex items-center gap-3 mb-2">
                    <StatusDot color="accent" pulse />
                    <span className="text-sm text-text-primary font-mono flex-1 truncate">
                      {job.model_id}
                    </span>
                    <span className="text-xs text-text-muted font-mono">{percent}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-bg-surface overflow-hidden mb-2">
                    <div
                      className="h-full rounded-full bg-accent transition-[width] duration-300"
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
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleCancel(job.model_id)}
                      aria-label={`Cancel download of ${job.model_id}`}
                    >
                      Cancel
                    </Button>
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
                <StatusDot color="warning" />
                <span className="text-sm text-text-primary font-mono flex-1 truncate">
                  {job.model_id}
                </span>
                <span className="text-xs text-text-muted">
                  Position: #{job.queue_position ?? "?"}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleCancel(job.model_id)}
                >
                  Cancel
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Completed */}
      {completed.length > 0 && (
        <div>
          <button
            onClick={() => setShowCompleted(!showCompleted)}
            className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-3"
          >
            Completed ({completed.length})
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className={`text-text-muted transition-transform duration-150 ${showCompleted ? "rotate-90" : ""}`}
            >
              <path d="M4 2l4 4-4 4" />
            </svg>
          </button>
          {showCompleted && (
            <div className="space-y-1">
              {completed.map(job => (
                <div key={job.job_id} className="flex items-center gap-3 px-3 py-2 text-sm">
                  <StatusDot color="success" />
                  <span className="text-text-primary font-mono flex-1 truncate">
                    {job.model_id}
                  </span>
                  <span className="text-xs text-text-muted">
                    {formatBytes(job.total_bytes)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Failed */}
      {failed.length > 0 && (
        <div>
          <button
            onClick={() => setShowFailed(!showFailed)}
            className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-3"
          >
            Failed ({failed.length})
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className={`text-text-muted transition-transform duration-150 ${showFailed ? "rotate-90" : ""}`}
            >
              <path d="M4 2l4 4-4 4" />
            </svg>
          </button>
          {showFailed && (
            <div className="space-y-1">
              {failed.map(job => (
                <Card key={job.job_id} className="p-3 flex items-center gap-3">
                  <StatusDot color="danger" />
                  <span className="text-sm text-text-primary font-mono flex-1 truncate">
                    {job.model_id}
                  </span>
                  <span className="text-xs text-danger max-w-[200px] truncate">
                    {job.error ?? "Unknown error"}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRetry(job.model_id)}
                  >
                    Retry
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
