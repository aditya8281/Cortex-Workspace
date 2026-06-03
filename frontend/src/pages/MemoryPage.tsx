import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useRepositoryProfiles } from "@/hooks/useIntelligence";
import { Brain } from "lucide-react";

async function searchMemory(q: string) {
  const res = await api.get("/intelligence/memory/search", { params: { q, limit: 20 } });
  return res.data.results as { id: number; category: string; title: string; content: string; source_path?: string }[];
}

export function MemoryPage() {
  const [query, setQuery] = useState("");
  const { data: repos = [] } = useRepositoryProfiles();
  const { data: results = [], isFetching } = useQuery({
    queryKey: ["memory-search", query],
    queryFn: () => searchMemory(query || "repository"),
    enabled: query.length > 1,
  });

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-cortex-accent-soft p-2 text-cortex-accent">
            <Brain className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Memory</h2>
            <p className="text-sm text-cortex-muted">Inspect what Cortex remembers across sessions.</p>
          </div>
        </div>

        <Input
          placeholder="Search memory…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Repository", repos.length],
            ["Discoveries", results.length],
            ["Categories", new Set(results.map((r) => r.category)).size],
          ].map(([label, count]) => (
            <Card key={label as string}>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-semibold">{count as number}</p>
                <p className="text-xs text-cortex-muted">{label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Memory entries</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {isFetching && <p className="text-sm text-cortex-muted">Searching…</p>}
            {results.map((entry) => (
              <div key={entry.id} className="rounded-lg border border-cortex-border p-3 text-sm">
                <div className="mb-1 flex items-center gap-2">
                  <Badge>{entry.category}</Badge>
                  <span className="font-medium">{entry.title}</span>
                </div>
                <p className="text-cortex-muted line-clamp-4">{entry.content}</p>
                {entry.source_path && (
                  <p className="mt-2 font-mono text-xs text-cortex-muted">{entry.source_path}</p>
                )}
              </div>
            ))}
            {!isFetching && results.length === 0 && (
              <p className="text-sm text-cortex-muted">Search or run sync to populate memory.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
