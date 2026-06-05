"use client";

import { useState, useRef, useEffect } from "react";
import { Card } from "@/components/ui/base";
import { memoryService } from "@/services/api/memory";
import { Search, Compass, AlertCircle, RefreshCw, FileText, ExternalLink } from "lucide-react";
import { useIsMounted } from "@/hooks/useIsMounted";

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useIsMounted();
  const abortRef = useRef<AbortController | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // cancel previous
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch (e) {}
      }
      const ac = new AbortController();
      abortRef.current = ac;
      const data = await memoryService.searchMemory(searchQuery, ac.signal);
      if (!mountedRef.current) return;
      setResults(data || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setError(message);
      console.error("Search error:", err);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  };

  // cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch (e) {}
      }
    };
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="border-b border-slate-800/60 pb-4">
        <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono flex items-center gap-2">
          <Compass className="text-cyan-400 w-5 h-5 animate-pulse" />
          Semantic Search Engine
        </h1>
        <p className="text-xs text-slate-400 font-sans mt-1">
          Perform high-performance vector semantic searches across all workspace repositories, codes, files, and annotations.
        </p>
      </div>

      {/* Search Bar Console */}
      <Card className="bg-slate-900/40 border-slate-800/80 p-4 rounded-xl">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="w-4 h-4 text-slate-500" />
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search concepts, variables, documentation blocks, files..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/40 font-sans shadow-inner transition-colors"
              disabled={loading}
            />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="px-5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs rounded-xl active:translate-y-[1px] transition-all shadow-[0_4px_12px_rgba(6,182,212,0.15)] shrink-0 flex items-center gap-1.5"
          >
            {loading ? <RefreshCw size={12} className="animate-spin" /> : <Search size={12} />}
            Search
          </button>
        </form>
      </Card>

      {error && (
        <Card className="bg-red-950/20 border border-red-900/30 p-4 rounded-xl flex items-start gap-2 text-red-400 text-xs">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{error}</p>
        </Card>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
          <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Scanning semantic vectors...</span>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-4">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider pl-1">
            FOUND {results.length} SEMANTIC MATCH{results.length > 1 ? "ES" : "ED RECORD"}
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            {results.map((result, idx) => {
              const titleText = result.title || result.name || "Unnamed Result";
              const summaryText = result.summary || result.content || result.description || "No description provided.";
              const scorePercent = result.score != null ? Number(result.score * 100).toFixed(0) : null;

              return (
                <div 
                  key={idx} 
                  className="bg-slate-900/30 hover:bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 rounded-xl p-5 relative overflow-hidden group shadow-[0_4px_12px_rgba(0,0,0,0.1)] transition-all duration-200"
                >
                  {/* Subtle top hover line */}
                  <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 min-w-0">
                      <div className="flex items-center gap-2">
                        <div className="p-1 bg-cyan-950/20 border border-cyan-900/30 text-cyan-400 rounded-lg">
                          <FileText size={12} />
                        </div>
                        <h3 className="font-semibold text-xs font-mono text-slate-200 truncate">{titleText}</h3>
                      </div>
                      
                      <p className="text-xs text-slate-400 leading-relaxed max-w-2xl line-clamp-3 group-hover:text-slate-300 transition-colors">
                        {summaryText}
                      </p>

                      {result.source_path && (
                        <div className="text-[9px] font-mono text-slate-500 flex items-center gap-1">
                          <span>LOCATION:</span>
                          <span className="text-slate-400 truncate max-w-md">{result.source_path}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2 shrink-0">
                      {scorePercent && (
                        <div className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-950/20 border border-cyan-900/30 px-2 py-0.5 rounded-full">
                          {scorePercent}% MATCH
                        </div>
                      )}
                      
                      {result.category && (
                        <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wide">
                          {result.category}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && searchQuery && results.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-12 text-center p-8 bg-slate-900/20 border border-dashed border-slate-800/60 rounded-2xl">
          <AlertCircle className="w-8 h-8 text-slate-600 mb-3" />
          <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-wide">No Semantic Matches</h3>
          <p className="text-xs text-slate-500 font-sans max-w-xs mt-1">
            We couldn't find any relevant code blocks matching "{searchQuery}". Try broadening your keywords.
          </p>
        </div>
      )}
    </div>
  );
}
