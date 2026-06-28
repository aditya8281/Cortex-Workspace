"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { StatusDot } from "@/shared/ui/StatusDot";
import { repository, type RepoEntry } from "../api";
import { IndexProgress } from "./IndexProgress";

interface RepoListItemProps {
  repo: RepoEntry;
  onGraph: (id: number) => void;
  onDelete: (id: number) => void;
}

function formatDate(dateStr: string): string {
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
  const [progress, setProgress] = useState(0);
  const [indexStatus, setIndexStatus] = useState("");
  const mountedRef = useRef(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
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
        setProgress(result.progress);
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

  const handleDelete = useCallback(async () => {
    setDeleting(true);
    try {
      await repository.delete(repo.id);
      if (mountedRef.current) onDelete(repo.id);
    } catch {
      if (mountedRef.current) setDeleting(false);
    }
  }, [repo.id, onDelete]);

  const primaryLanguage = repo.languages?.[0] ?? null;

  return (
    <Card className="space-y-3" role="article" aria-label={`Repository: ${repo.name}`}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <StatusDot color={repo.is_indexed ? "success" : "warning"} />
            <h3 className="truncate text-sm font-semibold text-text-primary">
              {repo.name}
            </h3>
          </div>
          <p className="truncate font-mono text-xs text-text-muted">{repo.path}</p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {primaryLanguage && <Badge variant="default">{primaryLanguage}</Badge>}
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-text-secondary">
        <span>{repo.file_count.toLocaleString()} files</span>
        <span>{repo.total_lines.toLocaleString()} lines</span>
        {repo.is_indexed && (
          <span>Indexed: {formatDate(repo.last_indexed)}</span>
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
        <Button
          size="sm"
          variant="danger"
          onClick={handleDelete}
          loading={deleting}
        >
          Delete
        </Button>
      </div>
    </Card>
  );
}
