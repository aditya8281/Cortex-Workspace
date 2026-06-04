"use client";

import { useState, useEffect } from "react";
import { Card, Badge } from "@/components/ui/base";
import { memoryService } from "@/services/api/memory";
import { Search, BrainCircuit, Calendar, HardDrive, Key, FileText, Download, Upload, AlertCircle, RefreshCw } from "lucide-react";

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const fetchMemories = async (searchQuery = "") => {
    try {
      setLoading(true);
      const data = await memoryService.searchMemory(searchQuery);
      setMemories(data);
    } catch (error) {
      console.error("Failed to fetch memories:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories("");
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetchMemories(query);
  };

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800/60 pb-4 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono flex items-center gap-2">
            <BrainCircuit className="text-cyan-400 w-5 h-5 animate-pulse" />
            Cognitive Memory Vault
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Access and query the semantic and structural memory indexed from your workspace codebase.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchMemories(query)}
            disabled={loading}
            className="p-2 bg-slate-900 border border-slate-800 text-slate-400 rounded-xl hover:text-white transition-all disabled:opacity-50 active:translate-y-[1px]"
            title="Refresh memory"
          >
            <RefreshCw size={14} className={loading ? "animate-spin text-cyan-400" : ""} />
          </button>
        </div>
      </div>

      {/* Search Console */}
      <Card className="bg-slate-900/40 border-slate-800/80 p-4 rounded-xl">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="w-4 h-4 text-slate-500" />
            </span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search concepts, variables, documentation blocks, files..."
              className="w-full pl-10 pr-4 py-2 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/40 font-sans shadow-inner transition-colors"
            />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="px-5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs rounded-xl active:translate-y-[1px] transition-all shadow-[0_4px_12px_rgba(6,182,212,0.15)] shrink-0"
          >
            Query Vault
          </button>
        </form>
      </Card>

      {/* Main Content Area */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
          <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Searching vectors...</span>
        </div>
      ) : memories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center p-8 bg-slate-900/20 border border-dashed border-slate-800/60 rounded-2xl">
          <AlertCircle className="w-8 h-8 text-slate-600 mb-3" />
          <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wide">No Entries Retreived</h3>
          <p className="text-xs text-slate-500 font-sans max-w-xs mt-1">
            Try a different search query or execute a Workspace Sync to build the semantic indexes.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider pl-1">
            RETRIEVED {memories.length} RELEVANT COGNITIVE ENTR{memories.length > 1 ? "IES" : "Y"}
          </div>

          <div className="grid grid-cols-1 gap-4">
            {memories.map((mem) => {
              const keyText = mem.key || mem.title || "Untitled Memory";
              const valText = mem.value || mem.content || "";
              const pathText = mem.source_path || null;

              return (
                <Card 
                  key={mem.id} 
                  className="bg-slate-900/30 hover:bg-slate-900/50 border-slate-800/80 hover:border-slate-700/80 transition-all duration-200 rounded-xl p-5 relative overflow-hidden group shadow-[0_4px_12px_rgba(0,0,0,0.1)]"
                >
                  {/* Subtle hover gradient border */}
                  <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="p-1.5 bg-cyan-950/20 border border-cyan-900/40 rounded-lg text-cyan-400">
                          {pathText ? <FileText size={13} /> : <Key size={13} />}
                        </div>
                        <h3 className="font-semibold text-sm text-slate-100 font-mono tracking-wide truncate max-w-lg">
                          {keyText}
                        </h3>
                      </div>
                      
                      <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap pl-0.5 group-hover:text-slate-300 transition-colors">
                        {valText}
                      </p>

                      {pathText && (
                        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 pt-1.5 border-t border-slate-900/40">
                          <HardDrive size={11} className="text-slate-600" />
                          <span className="truncate max-w-xl" title={pathText}>SOURCE: {pathText}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2 shrink-0">
                      {mem.category && (
                        <span className="text-[9px] font-mono font-bold tracking-wide uppercase px-2 py-0.5 bg-slate-950/60 border border-slate-800/60 rounded text-slate-400 group-hover:text-cyan-400 group-hover:border-cyan-500/20 transition-all">
                          {mem.category}
                        </span>
                      )}
                      
                      {mem.score !== undefined && (
                        <div className="text-[9px] font-mono text-slate-500">
                          Relevance: <span className="text-cyan-400 font-bold">{(mem.score * 100).toFixed(0)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
