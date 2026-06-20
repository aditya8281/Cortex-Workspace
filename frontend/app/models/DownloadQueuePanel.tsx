"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Download, X, RotateCcw, Clock, CheckCircle, AlertCircle } from "lucide-react";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import Skeleton from "@/shared/ui/Skeleton";
import { modelsApi } from "@/shared/api";
import { useSystemWebSocket } from "@/shared/hooks/useSystemWebSocket";
import type { DownloadJob } from "@/shared/types";

export default function DownloadQueuePanel() {
  const [active, setActive] = useState<DownloadJob[]>([]);
  const [queued, setQueued] = useState<DownloadJob[]>([]);
  const [completed, setCompleted] = useState<DownloadJob[]>([]);
  const [failed, setFailed] = useState<DownloadJob[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQueue = () => {
    modelsApi.downloadQueue()
      .then((data) => {
        setActive(data.active);
        setQueued(data.queued);
        setCompleted(data.completed);
        setFailed(data.failed);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchQueue(); }, []);

  useSystemWebSocket({
    path: "/ws/models",
    enabled: active.length > 0,
    onMessage(event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "model_progress") {
          fetchQueue();
        }
      } catch {}
    },
  });

  if (loading) {
    return <Skeleton className="h-48" />;
  }

  return (
    <div className="space-y-6">
      {/* Active Downloads */}
      {active.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text mb-3">
            Active Downloads ({active.length})
          </h3>
          <div className="space-y-3">
            {active.map((job) => (
              <DownloadJobCard key={job.job_id} job={job} onCancel={() => modelsApi.cancel(job.model_id)} />
            ))}
          </div>
        </div>
      )}

      {/* Queue */}
      {queued.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text mb-3">
            Queued ({queued.length})
          </h3>
          <div className="space-y-2">
            {queued.map((job) => (
              <Card key={job.job_id} className="p-3 flex items-center gap-3" gradient>
                <Clock size={14} className="text-text-muted" />
                <span className="text-sm text-text flex-1">{job.model_id}</span>
                <Badge variant="default">#{job.queue_position}</Badge>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Completed */}
      {completed.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text mb-3">
            Completed ({completed.length})
          </h3>
          <div className="space-y-2">
            {completed.slice(0, 5).map((job) => (
              <Card key={job.job_id} className="p-3 flex items-center gap-3" gradient>
                <CheckCircle size={14} className="text-success" />
                <span className="text-sm text-text flex-1">{job.model_id}</span>
                <Badge variant="success">Done</Badge>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Failed */}
      {failed.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text mb-3">
            Failed ({failed.length})
          </h3>
          <div className="space-y-2">
            {failed.map((job) => (
              <Card key={job.job_id} className="p-3 flex items-center gap-3" gradient>
                <AlertCircle size={14} className="text-danger" />
                <span className="text-sm text-text flex-1">{job.model_id}</span>
                <span className="text-xs text-danger">{job.error || "Unknown error"}</span>
                <Button variant="ghost" size="sm" onClick={() => modelsApi.download(job.model_id)}>
                  <RotateCcw size={12} />
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {active.length === 0 && queued.length === 0 && completed.length === 0 && failed.length === 0 && (
        <Card className="p-8 text-center" gradient>
          <Download size={40} className="text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text mb-2">No downloads</h3>
          <p className="text-sm text-text-secondary">
            Browse models and click download to get started.
          </p>
        </Card>
      )}
    </div>
  );
}

function DownloadJobCard({ job, onCancel }: { job: DownloadJob; onCancel: () => void }) {
  const percent = Math.round(job.progress * 100);
  const speedMB = job.speed_bytes_sec ? (job.speed_bytes_sec / 1024 / 1024).toFixed(1) : null;
  const etaMin = job.eta_seconds ? Math.ceil(job.eta_seconds / 60) : null;

  return (
    <Card className="p-4" gradient>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-text">{job.model_id}</span>
        <div className="flex items-center gap-2">
          {speedMB && (
            <span className="text-xs text-text-muted">{speedMB} MB/s</span>
          )}
          {etaMin && (
            <span className="text-xs text-text-muted">{etaMin}min left</span>
          )}
          <button onClick={onCancel} className="text-text-muted hover:text-danger transition-colors">
            <X size={14} />
          </button>
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-accent"
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-text-muted">
          {(job.downloaded_bytes / 1024 / 1024 / 1024).toFixed(1)}GB / {(job.total_bytes / 1024 / 1024 / 1024).toFixed(1)}GB
        </span>
        <span className="text-xs text-text-muted">{percent}%</span>
      </div>
    </Card>
  );
}
