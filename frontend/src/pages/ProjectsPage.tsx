import { useNavigate } from "react-router-dom";
import { ArrowRight, FolderGit2, RefreshCw, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLatestSyncRun, useRepositoryProfiles, useSyncStatus, useTriggerSync } from "@/hooks/useIntelligence";
import { formatTimestamp } from "@/lib/utils";

export function ProjectsPage() {
  const navigate = useNavigate();
  const { data: repos = [], isLoading } = useRepositoryProfiles();
  const { data: status } = useSyncStatus();
  const { data: latest } = useLatestSyncRun();
  const triggerSync = useTriggerSync();

  const projectCount = repos.length;
  const activeRoots = status?.discovery_roots?.length ?? 0;
  const indexedFiles = status?.tracked_files ?? 0;
  const lastSync = latest?.completed_at ? formatTimestamp(latest.completed_at) : formatTimestamp(status?.last_sync_time);

  return (
    <div className="h-full overflow-y-auto bg-cortex-bg p-4 md:p-6 lg:p-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <Card className="border-cortex-border/70 bg-cortex-surface/50">
          <CardContent className="grid gap-6 p-6 lg:grid-cols-[1.35fr_0.9fr] lg:items-center">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-cortex-accent/20 bg-cortex-accent-soft px-3 py-1 text-xs font-medium text-cortex-accent">
                <Sparkles className="h-3.5 w-3.5" />
                Project intelligence
              </div>
              <div>
                <h2 className="text-2xl font-semibold tracking-tight text-cortex-text md:text-3xl">
                  Living project spaces backed by real repositories
                </h2>
                <p className="mt-2 max-w-2xl text-sm text-cortex-muted">
                  Cortex groups discovered git roots into project-ready workspaces, keeps their summaries fresh during sync,
                  and surfaces the most relevant codebases without requiring manual curation.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="accent">{projectCount} projects</Badge>
                <Badge>{activeRoots} scan roots</Badge>
                <Badge variant="success">{indexedFiles} indexed files</Badge>
                <Badge variant={latest?.status === "running" ? "warn" : "default"}>
                  {latest?.status === "running" ? "Syncing now" : `Last sync ${lastSync}`}
                </Badge>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <Card className="border-cortex-border/60 bg-cortex-elevated/60">
                <CardContent className="p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-cortex-muted">Project count</p>
                  <p className="mt-2 text-2xl font-semibold tabular-nums">{projectCount}</p>
                </CardContent>
              </Card>
              <Card className="border-cortex-border/60 bg-cortex-elevated/60">
                <CardContent className="p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-cortex-muted">Scan roots</p>
                  <p className="mt-2 text-2xl font-semibold tabular-nums">{activeRoots}</p>
                </CardContent>
              </Card>
              <Card className="border-cortex-border/60 bg-cortex-elevated/60">
                <CardContent className="p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-cortex-muted">Indexed files</p>
                  <p className="mt-2 text-2xl font-semibold tabular-nums">{indexedFiles}</p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold tracking-tight">Discovered projects</h3>
            <p className="text-sm text-cortex-muted">Real repository profiles produced by the sync engine.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => triggerSync.mutate()} disabled={triggerSync.isPending} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Sync now
            </Button>
            <Button onClick={() => navigate("/repositories")} className="gap-2">
              Browse repositories
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="grid gap-4">
          {isLoading ? (
            <Card className="border-cortex-border/70 bg-cortex-surface/50">
              <CardContent className="space-y-3 p-6">
                <div className="h-4 w-40 rounded-full bg-cortex-border/80 animate-shimmer" />
                <div className="h-4 w-full rounded-full bg-cortex-border/60 animate-shimmer" />
                <div className="h-4 w-5/6 rounded-full bg-cortex-border/50 animate-shimmer" />
              </CardContent>
            </Card>
          ) : repos.length === 0 ? (
            <Card className="border-dashed border-cortex-border/80 bg-cortex-surface/40">
              <CardContent className="flex flex-col items-start gap-3 p-6">
                <FolderGit2 className="h-5 w-5 text-cortex-muted" />
                <div>
                  <h4 className="font-medium">No projects indexed yet</h4>
                  <p className="text-sm text-cortex-muted">
                    Run Sync Now to discover repositories and build project profiles automatically.
                  </p>
                </div>
                <Button variant="secondary" onClick={() => triggerSync.mutate()} disabled={triggerSync.isPending}>
                  Start sync
                </Button>
              </CardContent>
            </Card>
          ) : (
            repos.map((repo) => (
              <Card key={repo.path} className="border-cortex-border/70 bg-cortex-surface/50">
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <CardTitle className="flex items-center gap-2">
                        <FolderGit2 className="h-4 w-4 text-cortex-accent" />
                        <span className="truncate">{repo.name}</span>
                      </CardTitle>
                      <CardDescription className="mt-1 truncate">{repo.path}</CardDescription>
                    </div>
                    <Badge variant="accent">{repo.tech_stack || "Unclassified"}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-cortex-muted line-clamp-2">{repo.summary || "Project summary is building during sync."}</p>
                  <div className="flex flex-wrap gap-2">
                    <Badge>{repo.entry_points?.length ?? 0} entry points</Badge>
                    <Badge>{repo.important_files?.length ?? 0} important files</Badge>
                    <Badge>{repo.dependencies?.length ?? 0} dependencies</Badge>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="secondary" size="sm" onClick={() => navigate(`/repositories/${encodeURIComponent(repo.path)}`)}>
                      Open repository
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => navigate("/chat")}>
                      Ask Cortex about this project
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
