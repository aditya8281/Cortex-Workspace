"use client";

import { useState } from "react";
import { Card, Button, Input, Spinner } from "@/components/ui/base";
import { memoryService } from "@/services/api/memory";

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await memoryService.searchMemory(searchQuery);
      setResults(data || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setError(message);
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Search</h1>

      <Card>
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search your workspace..."
              disabled={loading}
            />
            <Button type="submit" loading={loading}>
              Search
            </Button>
          </div>
        </form>
      </Card>

      {error && (
        <Card className="bg-red-900/20 border border-red-700">
          <p className="text-red-400">{error}</p>
        </Card>
      )}

      {loading && <Spinner />}

      {!loading && results.length > 0 && (
        <Card>
          <h2 className="text-xl font-bold mb-4">Results ({results.length})</h2>
          <div className="space-y-3">
            {results.map((result, idx) => (
              <div key={idx} className="border border-border p-3 rounded bg-surface">
                <h3 className="font-medium text-white">{result.title || result.name || "Unnamed"}</h3>
                <p className="text-sm text-gray-400 mt-1 line-clamp-2">{result.summary || result.content || result.description || "No description"}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {!loading && searchQuery && results.length === 0 && !error && (
        <Card className="text-center text-gray-400">
          <p>No results found for "{searchQuery}"</p>
        </Card>
      )}
    </div>
  );
}

