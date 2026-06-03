import { FileText, GitBranch, Brain, Lightbulb, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useChatStore } from "@/stores/chatStore";
import { useRepositoryProfiles, useProactiveNotifications } from "@/hooks/useIntelligence";
import { cn } from "@/lib/utils";

const kindIcon = {
  file: FileText,
  repo: GitBranch,
  memory: Brain,
  document: FileText,
  concept: Lightbulb,
  activity: Activity,
};

export function ContextPanel() {
  const items = useChatStore((s) => s.contextItems);
  const { data: repos = [] } = useRepositoryProfiles();
  const { data: proactive = [] } = useProactiveNotifications();

  return (
    <aside className="hidden h-full w-[300px] shrink-0 flex-col border-l border-cortex-border bg-cortex-surface/60 backdrop-blur-md xl:flex">
      <div className="border-b border-cortex-border p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Context</p>
        <h2 className="text-sm font-medium">Live intelligence</h2>
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {items.length > 0 && (
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm">This conversation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 p-4 pt-0">
              {items.map((item) => {
                const Icon = kindIcon[item.kind];
                return (
                  <div key={item.id} className="flex gap-2 rounded-lg bg-cortex-elevated/80 p-2 text-xs">
                    <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cortex-accent" />
                    <div>
                      <p className="font-medium">{item.title}</p>
                      {item.detail && <p className="text-cortex-muted">{item.detail}</p>}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-sm">Relevant repositories</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 p-4 pt-0">
            {repos.slice(0, 4).map((repo) => (
              <div key={repo.path} className="rounded-lg border border-cortex-border p-2 text-xs">
                <p className="font-medium">{repo.name}</p>
                <p className="line-clamp-2 text-cortex-muted">{repo.summary}</p>
                <Badge variant="accent" className="mt-1">
                  {repo.tech_stack || "repo"}
                </Badge>
              </div>
            ))}
            {!repos.length && <p className="text-xs text-cortex-muted">Run sync to discover repositories.</p>}
          </CardContent>
        </Card>

        {proactive.length > 0 && (
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm">Observations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 p-4 pt-0">
              {proactive.slice(0, 3).map((n) => (
                <div
                  key={n.id}
                  className={cn(
                    "rounded-lg border p-2 text-xs",
                    n.priority === "high" ? "border-cortex-warn/40" : "border-cortex-border",
                  )}
                >
                  <p className="font-medium">{n.title}</p>
                  <p className="text-cortex-muted">{n.message}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </aside>
  );
}
