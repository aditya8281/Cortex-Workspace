"use client";

/**
 * DockedDownloadPanel — persistent bottom download panel.
 *
 * Shows active downloads with progress/speed/ETA, pause/resume/cancel controls.
 * Collapsible when active, hidden when no downloads.
 */
import { useState } from "react";
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
import { formatBytes, formatSpeed, formatEta } from "../api";
import { Button } from "@/shared/ui/Button";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DockedDownloadPanel() {
  const { state, actions } = useDownloadContext();
  const { active, queued, history, connected } = state;
  const [expanded, setExpanded] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  // Hide when no downloads and history not open
  if (active.length === 0 && queued.length === 0 && !showHistory) {
    return null;
  }

  const totalActive = active.length;
  const totalQueued = queued.length;
  const overallProgress = active.length > 0
    ? Math.round(active.reduce((sum, j) => sum + j.progress, 0) / active.length * 100)
    : 0;
  const topSpeed = active.reduce((max, j) => Math.max(max, j.speed_bytes_sec ?? 0), 0);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-border-subtle bg-bg-base/95 backdrop-blur-sm">
      {/* Collapsed bar */}
      {!expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-bg-surface/50 transition-colors"
          aria-label="Expand download panel"
        >
          <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
          <span className="text-text-primary font-medium">
            Downloads
          </span>
          {totalActive > 0 && (
            <span className="text-text-muted">
              ({totalActive} active{totalQueued > 0 ? `, ${totalQueued} queued` : ""})
            </span>
          )}
          <span className="ml-auto text-text-muted font-mono text-xs">
            {overallProgress}%{topSpeed > 0 && ` · ${formatSpeed(topSpeed)}`}
          </span>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted">
            <path d="M2 8l4-4 4 4" />
          </svg>
        </button>
      )}

      {/* Expanded panel */}
      {expanded && (
        <div className="max-h-[40vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border-subtle">
            <button
              onClick={() => setExpanded(false)}
              className="text-text-muted hover:text-text-primary transition-colors"
              aria-label="Collapse download panel"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 4l4 4 4-4" />
              </svg>
            </button>
            <span className="text-sm font-medium text-text-primary">
              Downloads
            </span>
            {totalActive > 0 && (
              <span className="text-xs text-text-muted">
                {totalActive} active{totalQueued > 0 ? `, ${totalQueued} queued` : ""}
              </span>
            )}
            <div className="ml-auto flex items-center gap-2">
              {!connected && (
                <StatusDot color="danger" />
              )}
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-xs text-text-muted hover:text-text-primary transition-colors"
              >
                History
              </button>
            </div>
          </div>

          {/* Download rows */}
          <div className="overflow-y-auto flex-1">
            {/* Active downloads */}
            {active.map(job => (
              <div key={job.job_id} className="px-4 py-3 border-b border-border-subtle last:border-0">
                <div className="flex items-center gap-3 mb-1.5">
                  <StatusDot color={job.status === "paused" ? "warning" : "accent"} pulse={job.status === "downloading"} />
                  <span className="text-sm text-text-primary font-mono flex-1 truncate">
                    {job.model_id}
                  </span>
                  <span className="text-xs text-text-muted font-mono">
                    {Math.round(job.progress * 100)}%
                  </span>
                  <span className="text-xs text-text-muted">
                    {formatSpeed(job.speed_bytes_sec ?? 0)}
                  </span>
                  <span className="text-xs text-text-muted w-16 text-right">
                    {formatEta(job.eta_seconds)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full bg-bg-surface overflow-hidden">
                    <div
                      className="h-full rounded-full bg-accent transition-[width] duration-300"
                      style={{ width: `${Math.round(job.progress * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    {job.status === "downloading" ? (
                      <button
                        onClick={() => actions.pause(job.job_id)}
                        className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-surface transition-colors"
                        aria-label={`Pause download of ${job.model_id}`}
                        title="Pause"
                      >
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                          <rect x="3" y="2" width="3" height="10" rx="0.5" />
                          <rect x="8" y="2" width="3" height="10" rx="0.5" />
                        </svg>
                      </button>
                    ) : job.status === "paused" ? (
                      <button
                        onClick={() => actions.resume(job.job_id)}
                        className="p-1 rounded text-text-muted hover:text-accent hover:bg-bg-surface transition-colors"
                        aria-label={`Resume download of ${job.model_id}`}
                        title="Resume"
                      >
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                          <path d="M3 1.5v11l9-5.5z" />
                        </svg>
                      </button>
                    ) : null}
                    <button
                      onClick={() => actions.cancel(job.model_id)}
                      className="p-1 rounded text-text-muted hover:text-danger hover:bg-bg-surface transition-colors"
                      aria-label={`Cancel download of ${job.model_id}`}
                      title="Cancel"
                    >
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M3 3l8 8M11 3l-8 8" />
                      </svg>
                    </button>
                  </div>
                </div>
                <div className="mt-1 text-[0.625rem] text-text-muted font-mono">
                  {formatBytes(job.downloaded_bytes)} / {formatBytes(job.total_bytes)}
                </div>
              </div>
            ))}

            {/* Queued section */}
            {queued.length > 0 && (
              <div className="px-4 py-2 border-b border-border-subtle">
                <span className="text-xs text-text-muted font-medium">Queued</span>
              </div>
            )}
            {queued.map(job => (
              <div key={job.job_id} className="px-4 py-2.5 flex items-center gap-3 border-b border-border-subtle last:border-0">
                <span className="text-xs text-text-muted font-mono w-6 text-center">
                  #{job.queue_position ?? "?"}
                </span>
                <span className="text-sm text-text-primary font-mono flex-1 truncate">
                  {job.model_id}
                </span>
                <button
                  onClick={() => actions.cancel(job.model_id)}
                  className="p-1 rounded text-text-muted hover:text-danger hover:bg-bg-surface transition-colors"
                  aria-label={`Cancel queued download of ${job.model_id}`}
                  title="Cancel"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M3 3l8 8M11 3l-8 8" />
                  </svg>
                </button>
              </div>
            ))}

            {/* History drawer */}
            {showHistory && history.length > 0 && (
              <div className="border-t border-border-subtle">
                <div className="px-4 py-2 flex items-center justify-between">
                  <span className="text-xs text-text-muted font-medium">History</span>
                  <button
                    onClick={() => actions.clearCompleted()}
                    className="text-xs text-text-muted hover:text-danger transition-colors"
                  >
                    Clear all
                  </button>
                </div>
                {history.map(item => (
                  <div key={item.job_id} className="px-4 py-2 flex items-center gap-3 text-sm border-b border-border-subtle last:border-0">
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
                      <span className="text-xs text-danger max-w-[150px] truncate">
                        {item.error}
                      </span>
                    )}
                    {item.status === "failed" && (
                      <button
                        onClick={() => actions.retry(item.model_id)}
                        className="text-xs text-accent hover:text-accent/80 transition-colors"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
