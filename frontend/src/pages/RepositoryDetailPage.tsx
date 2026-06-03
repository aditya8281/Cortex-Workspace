import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useRepositoryProfiles } from "@/hooks/useIntelligence";
import { useChatStore } from "@/stores/chatStore";
import { ArrowLeft } from "lucide-react";

export function RepositoryDetailPage() {
  const params = useParams();
  const encoded = params["*"] ?? params.path ?? "";
  const path = encoded ? decodeURIComponent(encoded) : "";
  const navigate = useNavigate();
  const { data: repos = [] } = useRepositoryProfiles();
  const repo = repos.find((r) => r.path === path);
  const newSession = useChatStore((s) => s.newSession);
  const setInput = useChatStore((s) => s.setInputQuery);

  if (!repo) {
    return (
      <div className="p-8 text-center text-sm text-cortex-muted">
        Repository not found.{" "}
        <button type="button" className="text-cortex-accent" onClick={() => navigate("/repositories")}>
          Back
        </button>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => navigate("/repositories")}>
          <ArrowLeft className="h-4 w-4" />
          Repositories
        </Button>

        <div>
          <h2 className="text-2xl font-semibold">{repo.name}</h2>
          <p className="text-sm text-cortex-muted">{repo.path}</p>
          <div className="mt-2 flex gap-2">
            <Badge variant="accent">{repo.tech_stack}</Badge>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={() => {
              newSession();
              setInput(`Analyze repository at ${repo.path} and explain its architecture.`);
              navigate("/chat");
            }}
          >
            Ask repository
          </Button>
          <Button variant="secondary" onClick={() => navigate("/graph")}>
            View in graph
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Summary</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">{repo.summary}</CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Architecture</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-cortex-muted">{repo.architecture_summary}</CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Dependencies</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-1">
              {repo.dependencies.slice(0, 20).map((d) => (
                <Badge key={d}>{d}</Badge>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Entry points</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1 text-sm font-mono">
              {repo.entry_points.map((e) => (
                <p key={e}>{e}</p>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Important files</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm font-mono">
            {repo.important_files.map((f) => (
              <p key={f}>{f}</p>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
