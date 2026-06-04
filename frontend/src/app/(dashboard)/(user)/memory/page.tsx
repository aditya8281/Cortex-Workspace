"use client";

import { useState, useEffect } from "react";
import { Button, Card, Spinner } from "@/components/ui/base";
import { memoryService } from "@/services/api/memory";
import type { MemoryItem } from "@/types/api";

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        setLoading(true);
        const data = await memoryService.searchMemory("");
        setMemories(data);
      } catch (error) {
        console.error("Failed to fetch memories:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchMemories();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const data = await memoryService.searchMemory(query);
      setMemories(data);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Memory Vault</h1>

      <Card>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memory..."
            className="flex-1 bg-background border border-border px-4 py-2 rounded text-white"
          />
          <Button type="submit">Search</Button>
        </form>
      </Card>

      <div className="space-y-2">
        {memories.map((mem) => (
          <Card key={mem.id} className="bg-background">
            <h3 className="font-medium">{mem.key}</h3>
            <p className="text-sm text-gray-400 mt-1">{mem.value}</p>
            {mem.category && <p className="text-xs text-gray-500 mt-2">Category: {mem.category}</p>}
          </Card>
        ))}
      </div>
    </div>
  );
}
