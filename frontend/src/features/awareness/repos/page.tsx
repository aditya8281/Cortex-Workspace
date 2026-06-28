"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { repository, type RepoEntry } from "../api";
import { AddRepoModal } from "../components/AddRepoModal";
import { RepoListItem } from "../components/RepoListItem";
import { GraphView } from "../components/GraphView";

export default function AwarenessReposPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [repos, setRepos] = useState<RepoEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedRepoId, setSelectedRepoId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRepos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await repository.list();
      setRepos(Array.isArray(result) ? result : result.items ?? []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load repositories",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth");
      return;
    }
    if (user) fetchRepos();
  }, [user, authLoading, router, fetchRepos]);

  // Auth guard — render nothing while checking
  if (authLoading || !user) return null;

  const handleAddSuccess = (repo: RepoEntry) => {
    setRepos((prev) => [...prev, repo]);
  };

  const handleDelete = (id: number) => {
    setRepos((prev) => prev.filter((r) => r.id !== id));
    if (selectedRepoId === id) setSelectedRepoId(null);
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">
              Repositories
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              Monitored repositories and their awareness state
            </p>
          </div>
          <Button onClick={() => setShowAddModal(true)}>
            Add Repository
          </Button>
        </div>

        {/* Error banner */}
        {error && !loading && (
          <div className="rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-28 w-full" />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && repos.length === 0 && !error && (
          <EmptyState
            title="No repositories"
            description="Add a repository to start monitoring its awareness state."
            action={
              <Button onClick={() => setShowAddModal(true)}>
                Add Repository
              </Button>
            }
          />
        )}

        {/* Repo list */}
        {!loading && repos.length > 0 && (
          <div className="space-y-3">
            {repos.map((repo) => (
              <div key={repo.id}>
                <RepoListItem
                  repo={repo}
                  onGraph={setSelectedRepoId}
                  onDelete={handleDelete}
                />
                {/* Inline GraphView when this repo is selected */}
                {selectedRepoId === repo.id && (
                  <div className="mt-2">
                    <GraphView
                      repoId={repo.id}
                      onClose={() => setSelectedRepoId(null)}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Add repo modal */}
        <AddRepoModal
          open={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSuccess={handleAddSuccess}
        />
      </div>
    </AppShell>
  );
}
