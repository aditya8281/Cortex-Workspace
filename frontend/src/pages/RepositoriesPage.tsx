import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useRepositoryProfiles } from "@/hooks/useIntelligence";
import { GitBranch } from "lucide-react";

export function RepositoriesPage() {
  const { data: repos = [], isLoading } = useRepositoryProfiles();

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h2 className="text-xl font-semibold">Repositories</h2>
          <p className="text-sm text-cortex-muted">Architecture intelligence stored by Cortex.</p>
        </div>

        {isLoading && <p className="text-sm text-cortex-muted">Loading repositories…</p>}

        <div className="grid gap-4">
          {repos.map((repo) => (
            <Link key={repo.path} to={`/repositories/${encodeURIComponent(repo.path)}`}>
              <Card className="transition hover:border-cortex-accent/40">
                <CardHeader className="flex flex-row items-start gap-3">
                  <div className="rounded-lg bg-cortex-accent-soft p-2 text-cortex-accent">
                    <GitBranch className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <CardTitle>{repo.name}</CardTitle>
                    <CardDescription className="truncate">{repo.path}</CardDescription>
                  </div>
                  <Badge variant="accent">{repo.tech_stack || "—"}</Badge>
                </CardHeader>
                <CardContent>
                  <p className="line-clamp-2 text-sm text-cortex-muted">{repo.summary}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
          {!isLoading && repos.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center text-sm text-cortex-muted">
                No repositories indexed yet. Open Sync Center and run Sync Now.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
