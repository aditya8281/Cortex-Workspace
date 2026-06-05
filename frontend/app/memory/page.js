"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, Input, Loader } from "../../src/shared/ui";

function formatClock(value) {
  if (!value) return "live";
  try {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(new Date(value));
  } catch {
    return "live";
  }
}

function MemoryCard({ entry }) {
  return (
    <div className="relative grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 pl-cortex-16">
      <div className="absolute left-0 top-4 h-2.5 w-2.5 -translate-x-1/2 rounded-full border border-cortex-cyan bg-cortex-bg shadow-cortex-cyan" />
      <div className="flex flex-wrap items-center gap-cortex-8">
        <Badge variant="cyan">{entry.category || "memory"}</Badge>
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
          {formatClock(entry.updated_at || entry.created_at)}
        </span>
        {entry.source_path ? (
          <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
            {entry.source_path}
          </span>
        ) : null}
      </div>
      <div className="text-base font-medium text-cortex-text">{entry.title}</div>
      <div className="font-mono text-sm leading-6 text-cortex-text-muted">{entry.content}</div>
    </div>
  );
}

export default function MemoryPage() {
  const [memory, setMemory] = useState({ entries: [], categories: {}, count: 0 });
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("note");
  const [sourcePath, setSourcePath] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadMemory() {
    try {
      const response = await fetch("/api/memory?limit=24", { cache: "no-store" });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "Memory request failed");
      }

      setMemory(data);
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Memory request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMemory();
    const timer = window.setInterval(loadMemory, 8000);
    return () => window.clearInterval(timer);
  }, []);

  async function submitMemory(event) {
    event.preventDefault();
    if (!title.trim() || !content.trim()) {
      setError("SYSTEM ERROR: Title and content are required.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const response = await fetch("/api/memory", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: title.trim(),
          content: content.trim(),
          category: category.trim() || "note",
          source_path: sourcePath.trim() || null,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || data?.detail || "Memory write failed");
      }

      setTitle("");
      setContent("");
      setSourcePath("");
      await loadMemory();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Memory write failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="grid gap-cortex-16">
      <div className="flex items-start justify-between gap-cortex-16">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Memory</p>
          <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Persistent Memory Timeline</h1>
          <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
            Structured memory archive separated from chat. This surface is for stored context, notes, and indexed observations.
          </p>
        </div>
        <div className="flex items-center gap-cortex-12">
          <Badge variant="cyan">{memory.count || 0} entries</Badge>
          <Button variant="secondary" size="sm" onClick={loadMemory} disabled={loading}>
            {loading ? (
              <span className="inline-flex items-center gap-cortex-8">
                <Loader className="h-3.5 w-3.5" />
                Syncing
              </span>
            ) : (
              "Refresh"
            )}
          </Button>
        </div>
      </div>

      {error ? (
        <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
          <div className="font-mono text-sm">Error: {error}</div>
        </Card>
      ) : null}

      <div className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.4fr)_360px]">
        <Card className="grid gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Timeline</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Memory stream</h2>
            </div>
            <Badge variant="neutral">{Object.keys(memory.categories || {}).length} categories</Badge>
          </div>

          <div className="relative grid gap-cortex-12 pl-2">
            <div className="absolute left-1 top-0 h-full w-px bg-cortex-border" />
            {memory.entries?.length > 0 ? (
              memory.entries.map((entry) => <MemoryCard key={entry.id} entry={entry} />)
            ) : (
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                No memory entries stored yet.
              </div>
            )}
          </div>
        </Card>

        <div className="grid gap-cortex-16">
          <Card className="grid gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Archive control</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Store memory entry</h2>
            </div>

            <form className="grid gap-cortex-12" onSubmit={submitMemory}>
              <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Memory title" />
              <Input
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                placeholder="Category"
                spellCheck={false}
              />
              <Input
                value={sourcePath}
                onChange={(event) => setSourcePath(event.target.value)}
                placeholder="Source path"
                spellCheck={false}
              />
              <textarea
                value={content}
                onChange={(event) => setContent(event.target.value)}
                placeholder="Memory content"
                rows={7}
                className="w-full rounded-cortex border border-cortex-border bg-cortex-bg-secondary px-cortex-16 py-cortex-12 font-mono text-sm text-cortex-text outline-none transition duration-cortex focus:border-cortex-cyan/35 focus:shadow-cortex-cyan"
              />
              <Button type="submit" variant="primary" disabled={submitting}>
                {submitting ? "Storing..." : "Store memory"}
              </Button>
            </form>
          </Card>

          <Card className="grid gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Categories</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Memory index</h2>
            </div>

            <div className="grid gap-cortex-8">
              {Object.entries(memory.categories || {}).length > 0 ? (
                Object.entries(memory.categories).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 px-cortex-12 py-cortex-8 font-mono text-sm text-cortex-text-muted"
                  >
                    <span className="uppercase tracking-[0.12em]">{key}</span>
                    <span>{value}</span>
                  </div>
                ))
              ) : (
                <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                  No categories indexed yet.
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
