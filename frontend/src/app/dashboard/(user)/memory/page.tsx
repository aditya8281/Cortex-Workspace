"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/base";
import { ErrorMessage } from "@/components/shared/ErrorDisplay";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { memoryService } from "@/services/api/memory";
import { Search, BrainCircuit, HardDrive, Key, FileText, AlertCircle, RefreshCw } from "lucide-react";

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [knowledgeList, setKnowledgeList] = useState<any[]>([]);
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [openKnowledgeId, setOpenKnowledgeId] = useState<number | null>(null);

  const fetchMemories = async (searchQuery = "") => {
    try {
      setError(null);
      const data = await memoryService.searchMemory(searchQuery);
      setMemories(data || []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch memories";
      setError(msg);
      console.error("Failed to fetch memories:", err);
    }
  };

  const fetchKnowledge = async () => {
    try {
      const data = await memoryService.getKnowledge();
      setKnowledgeList(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch knowledge list:", err);
    }
  };

  const fetchActivity = async () => {
    try {
      const data = await memoryService.getProactiveNotifications();
      setActivityFeed(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch activity feed:", err);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchMemories(""), fetchKnowledge(), fetchActivity()]);
      setLoading(false);
    };
    init();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetchMemories(query);
  };

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800/60 pb-4 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono flex items-center gap-2">
            <BrainCircuit className="text-cyan-400 w-5 h-5 animate-pulse" />
            Cognitive Memory Vault
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-1">Access and query the semantic and structural memory indexed from your workspace codebase.</p>
        </div>

        <div className="flex items-center gap-2">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="w-4 h-4 text-slate-500" />
              </span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search memories..."
                className="pl-10 pr-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white text-xs rounded-xl"
            >
              Query
            </button>
            <button
              type="button"
              onClick={() => fetchMemories(query)}
              className="px-3 py-2 bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-xl"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: search results / memories */}
        <div className="lg:col-span-2">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Loading memories...</span>
            </div>
          )}

          {!loading && error && <ErrorMessage message={error} />}

          {!loading && !error && memories.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center p-8 bg-slate-900/20 border border-dashed border-slate-800/60 rounded-2xl">
              <AlertCircle className="w-8 h-8 text-slate-600 mb-3" />
              <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wide">No Entries Retrieved</h3>
              <p className="text-xs text-slate-500 font-sans max-w-xs mt-1">Try a different search query or run a Workspace Sync to build the semantic indexes.</p>
            </div>
          )}

          {!loading && !error && memories.length > 0 && (
            <div className="space-y-4">
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider pl-1">RETRIEVED {memories.length} RELEVANT MEMORIES</div>
              <div className="grid grid-cols-1 gap-4">
                {memories.map((mem) => (
                  <Card key={mem.id} className="bg-slate-900/30 border-slate-800/80 rounded-xl p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <div className="p-1.5 bg-cyan-950/20 border border-cyan-900/40 rounded-lg text-cyan-400">
                            {mem.source_path ? <FileText size={13} /> : <Key size={13} />}
                          </div>
                          <h3 className="font-semibold text-sm text-slate-100 font-mono truncate">{mem.title || mem.key || 'Untitled'}</h3>
                        </div>

                        <p className="text-xs text-slate-400 mt-2 whitespace-pre-wrap">{mem.content}</p>

                        {mem.source_path && (
                          <div className="text-[10px] font-mono text-slate-500 mt-2">Source: {mem.source_path}</div>
                        )}
                      </div>

                      <div className="flex flex-col items-end gap-2">
                        {mem.score !== undefined && <div className="text-[10px] text-slate-400">{Number((mem.score ?? 0) * 100).toFixed(0)}% relevance</div>}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: knowledge + activity */}
        <aside className="space-y-4">
          <Card className="p-4">
            <h4 className="text-xs font-mono text-slate-400 uppercase">Knowledge (recent)</h4>
            <div className="mt-3 space-y-2 max-h-56 overflow-y-auto">
              {knowledgeList.length === 0 ? (
                <div className="text-xs text-slate-500">No knowledge entries found.</div>
              ) : (
                knowledgeList.map((k: any) => (
                  <div key={k.id} className="p-2 bg-slate-950/30 border border-slate-800 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-mono text-slate-200 truncate">{k.title}</div>
                      <button onClick={() => setOpenKnowledgeId(openKnowledgeId === k.id ? null : k.id)} className="text-xs text-cyan-400">{openKnowledgeId === k.id ? "Hide" : "View"}</button>
                    </div>
                    {openKnowledgeId === k.id && <div className="mt-2 text-xs text-slate-400 whitespace-pre-wrap">{k.summary || k.content || "(no summary)"}</div>}
                  </div>
                ))
              )}
            </div>
          </Card>

          <Card className="p-4">
            <h4 className="text-xs font-mono text-slate-400 uppercase">Activity Feed</h4>
            <div className="mt-3 space-y-2 max-h-56 overflow-y-auto text-xs text-slate-400">
              {activityFeed.length === 0 ? (
                <div>No recent activity.</div>
              ) : (
                activityFeed.map((a: any, idx: number) => (
                  <div key={idx} className="p-2 border border-slate-800 rounded-lg bg-slate-950/20">
                    <div className="font-mono text-[11px] text-slate-200 truncate">{a.title || a.message || JSON.stringify(a)}</div>
                    <div className="text-[10px] text-slate-500 mt-1">{a.summary || a.description || ""}</div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </aside>
      </div>
      </div>
    </ErrorBoundary>
  );
}
