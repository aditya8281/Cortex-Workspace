"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Download,
  X,
  RotateCcw,
  Clock,
  CheckCircle,
  AlertCircle,
  Pause,
  Trash2,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import Skeleton from "@/shared/ui/Skeleton";
import { modelsApi } from "@/shared/api";
import { useSystemWebSocket } from "@/shared/hooks/useSystemWebSocket";
import { useAuth } from "@/shared/auth/AuthProvider";
import type { DownloadJob } from "@/shared/types";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function formatEta(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const min = Math.ceil(seconds / 60);
  if (min < 60) return `${min}min`;
  const hr = Math.floor(min / 60);
  return `${hr}h ${min % 60}min`;
}

export default function DownloadManagerPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [active, setActive] = useState<DownloadJob[]>([]);
  const [queued, setQueued] = useState<DownloadJob[]>([]);
  const [completed, setCompleted] = useState<DownloadJob[]>([]);
  const [failed, setFailed] = useState<DownloadJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  const fetchQueue = () => {
    modelsApi
      .downloadQueue()
      .then((data) => {
        setActive(data.active);
        setQueued(data.queued);
        setCompleted(data.completed);
        setFailed(data.failed);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  useSystemWebSocket({
    path: "/ws/models",
    enabled: active.length > 0,
    onMessage(event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "model_progress") {
          fetchQueue();
        }
      } catch {
        /* ignore */
      }
    },
  });

  const totalActive = active.length;
  const totalQueued = queued.length;
  const totalCompleted = completed.length;
  const totalFailed = failed.length;

  const totalDownloaded = useMemo(
    () => completed.reduce((sum, j) => sum + j.total_bytes, 0),
    [completed]
  );
  const totalRemaining = useMemo(() => {
    const activeRemaining = active.reduce(
      (sum, j) => sum + (j.total_bytes - j.downloaded_bytes),
      0
    );
    const queuedTotal = queued.reduce((sum, j) => sum + j.total_bytes, 0);
    return activeRemaining + queuedTotal;
  }, [active, queued]);
  const maxEta = useMemo(() => {
    const etas = active.map((j) => j.eta_seconds ?? 0).filter(Boolean);
    return etas.length > 0 ? Math.max(...etas) : 0;
  }, [active]);
  const totalSpeed = useMemo(
    () => active.reduce((sum, j) => sum + (j.speed_bytes_sec ?? 0), 0),
    [active]
  );

  const hasDownloads = totalActive + totalQueued + totalCompleted + totalFailed > 0;

  if (authLoading || !user) return null;

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-6"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
              <Download size={24} className="text-accent" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-text">Download Manager</h1>
              <p className="text-sm text-text-secondary">
                Manage all model downloads in one place
              </p>
            </div>
          </div>

          {/* Status Badges */}
          <div className="flex flex-wrap items-center gap-2 mt-4">
            {totalActive > 0 && (
              <Badge variant="accent">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent animate-pulse mr-1.5" />
                {totalActive} Active
              </Badge>
            )}
            {totalQueued > 0 && (
              <Badge variant="default">
                <Clock size={10} className="mr-1" />
                {totalQueued} Queued
              </Badge>
            )}
            {totalCompleted > 0 && (
              <Badge variant="success">
                <CheckCircle size={10} className="mr-1" />
                {totalCompleted} Done
              </Badge>
            )}
            {totalFailed > 0 && (
              <Badge variant="danger">
                <AlertCircle size={10} className="mr-1" />
                {totalFailed} Failed
              </Badge>
            )}
          </div>
        </motion.div>

        {loading ? (
          <div className="space-y-6">
            <Skeleton className="h-16" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </div>
        ) : !hasDownloads ? (
          <Card className="p-8 text-center" gradient>
            <Download size={40} className="text-text-muted mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-text mb-2">No downloads</h3>
            <p className="text-sm text-text-secondary">
              Browse models and click download to get started.
            </p>
          </Card>
        ) : (
          <div className="space-y-8">
            {/* Summary Bar */}
            {(totalActive > 0 || totalQueued > 0) && (
              <Card className="p-4" gradient>
                <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Download size={14} className="text-accent" />
                    <span className="text-text-secondary">Downloaded</span>
                    <span className="font-mono text-text font-medium">
                      {formatBytes(totalDownloaded)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={14} className="text-text-muted" />
                    <span className="text-text-secondary">Remaining</span>
                    <span className="font-mono text-text font-medium">
                      {formatBytes(totalRemaining)}
                    </span>
                  </div>
                  {maxEta > 0 && (
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-text-muted" />
                      <span className="text-text-secondary">ETA</span>
                      <span className="font-mono text-text font-medium">
                        ~{formatEta(maxEta)}
                      </span>
                    </div>
                  )}
                  {totalSpeed > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="text-text-secondary">Speed</span>
                      <span className="font-mono text-text font-medium">
                        {formatBytes(totalSpeed)}/s
                      </span>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Active Downloads */}
            {active.length > 0 && (
              <section>
                <h2 className="text-xs font-mono uppercase tracking-wider text-text-muted mb-3">
                  Active Downloads
                </h2>
                <div className="space-y-3">
                  {active.map((job) => (
                    <ActiveDownloadCard
                      key={job.job_id}
                      job={job}
                      onCancel={() => modelsApi.cancel(job.model_id).then(fetchQueue)}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Queued */}
            {queued.length > 0 && (
              <section>
                <h2 className="text-xs font-mono uppercase tracking-wider text-text-muted mb-3">
                  Queued
                </h2>
                <div className="space-y-2">
                  {queued.map((job, i) => (
                    <Card key={job.job_id} className="p-3 flex items-center gap-3" gradient>
                      <span className="text-xs font-mono text-text-muted w-5 text-center">
                        {i + 1}
                      </span>
                      <Clock size={14} className="text-text-muted shrink-0" />
                      <span className="text-sm text-text flex-1 truncate">
                        {job.model_id}
                      </span>
                      <span className="text-xs text-text-muted shrink-0">
                        {formatBytes(job.total_bytes)}
                      </span>
                      <button
                        onClick={() =>
                          modelsApi.cancel(job.model_id).then(fetchQueue)
                        }
                        className="text-text-muted hover:text-danger transition-colors shrink-0"
                        title="Remove from queue"
                      >
                        <X size={14} />
                      </button>
                    </Card>
                  ))}
                </div>
              </section>
            )}

            {/* Completed */}
            {completed.length > 0 && (
              <section>
                <h2 className="text-xs font-mono uppercase tracking-wider text-text-muted mb-3">
                  Completed
                </h2>
                <div className="space-y-2">
                  {completed.map((job) => (
                    <Card
                      key={job.job_id}
                      className="p-3 flex items-center gap-3 border-success/12"
                      gradient
                    >
                      <CheckCircle size={14} className="text-success shrink-0" />
                      <span className="text-sm text-text flex-1 truncate">
                        {job.model_id}
                      </span>
                      <span className="text-xs text-text-muted shrink-0">
                        {formatBytes(job.total_bytes)}
                      </span>
                      <button
                        onClick={() =>
                          modelsApi
                            .delete(job.model_id)
                            .then(fetchQueue)
                            .catch(() => {})
                        }
                        className="text-text-muted hover:text-danger transition-colors shrink-0"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    </Card>
                  ))}
                </div>
              </section>
            )}

            {/* Failed */}
            {failed.length > 0 && (
              <section>
                <h2 className="text-xs font-mono uppercase tracking-wider text-text-muted mb-3">
                  Failed
                </h2>
                <div className="space-y-2">
                  {failed.map((job) => (
                    <Card
                      key={job.job_id}
                      className="p-3 flex items-center gap-3 border-danger/20"
                      gradient
                    >
                      <AlertCircle size={14} className="text-danger shrink-0" />
                      <span className="text-sm text-text flex-1 truncate">
                        {job.model_id}
                      </span>
                      <span className="text-xs text-danger shrink-0 max-w-[200px] truncate">
                        {job.error || "Unknown error"}
                      </span>
                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            modelsApi.download(job.model_id).then(fetchQueue)
                          }
                          title="Retry"
                        >
                          <RotateCcw size={12} />
                        </Button>
                        <button
                          onClick={() =>
                            modelsApi.cancel(job.model_id).then(fetchQueue)
                          }
                          className="text-text-muted hover:text-danger transition-colors p-1"
                          title="Dismiss"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    </Card>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

function ActiveDownloadCard({
  job,
  onCancel,
}: {
  job: DownloadJob;
  onCancel: () => void;
}) {
  const percent = Math.round(job.progress * 100);
  const speedMB = job.speed_bytes_sec
    ? (job.speed_bytes_sec / 1024 / 1024).toFixed(1)
    : null;
  const etaMin = job.eta_seconds ? formatEta(job.eta_seconds) : null;

  return (
    <Card className="p-4 border-accent/20" gradient>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
            <Download size={16} className="text-accent" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-text truncate">{job.model_id}</p>
            <p className="text-xs text-text-muted">
              {formatBytes(job.total_bytes)} total
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {speedMB && (
            <span className="text-xs font-mono text-text-muted">
              {speedMB} MB/s
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={onCancel} title="Cancel">
            <X size={14} />
          </Button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden mb-2">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-accent to-accent-bright"
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted font-mono">
          {formatBytes(job.downloaded_bytes)} / {formatBytes(job.total_bytes)}
        </span>
        <div className="flex items-center gap-3">
          {etaMin && (
            <span className="text-xs text-text-muted">
              ~{etaMin}
            </span>
          )}
          <span className="text-xs font-mono text-accent font-medium">
            {percent}%
          </span>
        </div>
      </div>
    </Card>
  );
}
