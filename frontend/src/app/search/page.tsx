"use client";

import { useState } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { memorySearch, type SearchResult } from "@/features/memory/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"search" | "ask">("search");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      if (mode === "ask") {
        const res = await memorySearch.answer({ query });
        setAnswer(res.answer);
        setResults(Array.isArray(res.sources) ? res.sources : []);
      } else {
        const res = await memorySearch.search({ query, limit: 20 });
        setResults(Array.isArray(res) ? res : res.items ?? []);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-headline font-semibold text-text-primary">Universal Search</h1>
          <p className="text-sm text-text-secondary mt-1">Full-text and semantic search across all memory types</p>
        </div>

        {/* Search Bar */}
        <div className="flex items-end gap-3 mb-6">
          <div className="flex-1">
            <Input
              label={mode === "ask" ? "Ask a question" : "Search query"}
              placeholder={mode === "ask" ? "What do you want to know?" : "Search across episodic, semantic, working memory..."}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMode(mode === "search" ? "ask" : "search")}
            >
              {mode === "search" ? "Ask AI" : "Search"}
            </Button>
            <Button onClick={handleSearch} disabled={loading || !query.trim()}>
              {loading ? "Searching..." : "Go"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {/* Answer (Ask mode) */}
        {answer && (
          <Card className="p-5 mb-6 border-accent/20">
            <div className="flex items-start gap-3">
              <div className="h-7 w-7 rounded-md bg-accent/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-accent">
                  <path d="M7 1v2M7 11v2M1 7h2M11 7h2M3.05 3.05l1.41 1.41M9.54 9.54l1.41 1.41M3.05 10.95l1.41-1.41M9.54 4.46l1.41-1.41" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary mb-1">Answer</p>
                <p className="text-sm text-text-secondary leading-relaxed">{answer}</p>
                <p className="text-xs text-text-muted mt-2">{results.length} sources used</p>
              </div>
            </div>
          </Card>
        )}

        {/* Results */}
        <div className="space-y-3">
          {results.map((r, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-text-primary leading-relaxed">{r.content}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <Badge variant="default">{r.memory_type}</Badge>
                    <span className="text-xs text-text-muted">relevance: {(r.score * 100).toFixed(0)}%</span>
                    <span className="text-xs text-text-muted">importance: {(r.importance * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
          {results.length === 0 && query && !loading && !answer && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="h-10 w-10 rounded-lg bg-bg-surface flex items-center justify-center mb-3">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted">
                  <circle cx="8" cy="8" r="5.5" />
                  <path d="M12.5 12.5L16 16" />
                </svg>
              </div>
              <p className="text-sm text-text-secondary">No results found for this query</p>
            </div>
          )}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </div>
        )}
      </div>
    </AppShell>
  );
}
