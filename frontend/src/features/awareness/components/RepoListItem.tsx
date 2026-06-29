"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { StatusDot } from "@/shared/ui/StatusDot";
import { repository, type RepoInfo } from "../api";
import { IndexProgress } from "./IndexProgress";
import { useToast } from "@/shared/ui/Toast";

interface RepoListItemProps {
  repo: RepoInfo;
  onGraph: (id: number) => void;
  onDelete: (id: number) => void;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Never";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function RepoListItem({ repo, onGraph, onDelete }: RepoListItemProps) {
  const [indexing, setIndexing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [progress, setProgress] = useState(0);
  const [indexStatus, setIndexStatus] = useState("");
  const mountedRef = useRef(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const confirmTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (confirmTimerRef.current) clearTimeout(confirmTimerRef.current);
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    intervalRef.current = setInterval(async () => {
      try {
        const result = await repository.indexStatus(repo.id);
        if (!mountedRef.current) return;
        setProgress(result.total_files > 0 ? Math.round((result.indexed_files / result.total_files) * 100) : 0);
        setIndexStatus(result.status);
        if (result.status === "indexed" || result.status === "error") {
          stopPolling();
          // Keep indexing state briefly so user sees the final state
          setTimeout(() => {
            if (mountedRef.current) setIndexing(false);
          }, 1500);
        }
      } catch {
        stopPolling();
        if (mountedRef.current) {
          setIndexStatus("error");
          setTimeout(() => {
            if (mountedRef.current) setIndexing(false);
          }, 1500);
        }
      }
    }, 2000);
  }, [repo.id, stopPolling]);

  const handleIndex = useCallback(async () => {
    setIndexing(true);
    setProgress(0);
    setIndexStatus("starting");
    try {
      await repository.index(repo.id);
      if (mountedRef.current) {
        startPolling();
      }
    } catch {
      if (mountedRef.current) {
        setIndexStatus("error");
        setTimeout(() => {
          if (mountedRef.current) setIndexing(false);
        }, 1500);
      }
    }
  }, [repo.id, startPolling]);

  const handleDeleteClick = useCallback(() => {
    if (confirmDelete) {
      // Second click — execute delete
      if (confirmTimerRef.current) clearTimeout(confirmTimerRef.current);
      setConfirmDelete(false);
      setDeleting(true);
      repository.delete(repo.id).then(() => {
        if (mountedRef.current) onDelete(repo.id);
      }).catch(() => {
        if (mountedRef.current) {
          setDeleting(false);
          toast("Failed to delete repository", "error");
        }
      });
    } else {
      // First click — show confirmation, auto-reset after 4 seconds
      setConfirmDelete(true);
      confirmTimerRef.current = setTimeout(() => {
        if (mountedRef.current) setConfirmDelete(false);
      }, 4000);
    }
  }, [repo.id, onDelete, confirmDelete]);

  const primaryLanguage = repo.primary_language;

  return (
    <Card className="space-y-3" role="article" aria-label={`Repository: ${repo.repo_name}`}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <StatusDot color={repo.status === "indexed" ? "success" : "warning"} />
            <h3 className="truncate text-sm font-semibold text-text-primary">
              {repo.repo_name}
            </h3>
          </div>
          <p className="truncate font-mono text-xs text-text-muted">{repo.repo_path}</p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {primaryLanguage && <Badge variant="default">{primaryLanguage}</Badge>}
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-text-secondary">
        <span>{repo.total_files.toLocaleString()} files</span>
        {repo.status === "indexed" && (
          <span>Indexed: {formatDate(repo.last_indexed_at)}</span>
        )}
      </div>

      {/* Progress bar while indexing */}
      {indexing && (
        <IndexProgress progress={progress} status={indexStatus} />
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1">
        <Button
          size="sm"
          variant="ghost"
          onClick={handleIndex}
          disabled={indexing}
        >
          {indexing ? "Indexing..." : "Index"}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => onGraph(repo.id)}>
          Graph
        </Button>
        {confirmDelete ? (
          <Button
            size="sm"
            variant="danger"
            onClick={handleDeleteClick}
            loading={deleting}
          >
            Confirm?
          </Button>
        ) : (
          <Button
            size="sm"
            variant="danger"
            onClick={handleDeleteClick}
            loading={deleting}
          >
            Delete
          </Button>
        )}
      </div>
    </Card>
  );
}
