"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles, ExternalLink, Code, Brain, FileText } from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import { Card } from "@/shared/ui/Card";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import { searchApi } from "@/shared/api";
import { cn } from "@/lib/utils";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [aiAnswer, setAiAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) return;
      setLoading(true);
      setHasSearched(true);
      try {
        const data = await searchApi.unified(q, { max_results: 20 });
        setResults(data.results || []);

        // Fetch LLM-powered answer from backend
        try {
          const answerRes = await searchApi.answer(q, { max_results: 10 });
          setAiAnswer(answerRes.answer || "No answer generated.");
        } catch {
          // Fallback to client-side synthesized answer
          if (data.results?.length > 0) {
            const sources = data.results
              .slice(0, 5)
              .map((r: any, i: number) => `[${i + 1}] ${r.title || r.file_path || "Result"}`)
              .join("\n");
            setAiAnswer(`Found ${data.results.length} relevant results across your codebase and memories.\n\nTop sources:\n${sources}`);
          } else {
            setAiAnswer("No results found for this query. Try rephrasing or checking your indexed repositories.");
          }
        }
      } catch {
        setAiAnswer("Search failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Hero Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-semibold text-text mb-2">Search your workspace</h1>
          <p className="text-text-secondary">
            Ask anything about your code, memories, or files
          </p>
        </motion.div>

        {/* Conversational Search Input */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch(query)}
              placeholder="Ask anything about your code, memories, or files..."
              className="w-full h-14 pl-12 pr-24 rounded-2xl border border-border-subtle bg-bg-elevated text-text placeholder:text-text-muted text-lg focus:outline-none focus:border-accent/30 focus:shadow-glow transition-all"
            />
            <button
              onClick={() => handleSearch(query)}
              disabled={loading || !query.trim()}
              className={cn(
                "absolute right-2 top-1/2 -translate-y-1/2",
                "px-4 py-2 rounded-xl font-medium text-sm",
                "bg-accent text-void hover:bg-accent-hover",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-colors"
              )}
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </motion.div>

        {/* AI Answer Panel */}
        {hasSearched && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Card className="p-6" gradient>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={18} className="text-accent" />
                <span className="text-sm font-semibold text-text">AI Answer</span>
              </div>
              <div className="text-text-secondary whitespace-pre-wrap leading-relaxed">
                {aiAnswer}
              </div>
            </Card>
          </motion.div>
        )}

        {/* Sources */}
        {hasSearched && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
              <span>Sources</span>
              <span className="text-xs text-text-muted bg-bg-surface px-2 py-0.5 rounded-full">
                {results.length}
              </span>
            </h3>
            <div className="space-y-2">
              {results.map((result: any, i: number) => (
                <Card key={i} hover className="p-4" gradient>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                      {result.type === "code" ? (
                        <Code size={14} className="text-accent" />
                      ) : result.type === "memory" ? (
                        <Brain size={14} className="text-accent" />
                      ) : (
                        <FileText size={14} className="text-accent" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-text truncate">
                          {result.title || result.file_path || "Result"}
                        </span>
                        <span className="text-xs text-text-muted shrink-0">
                          [{i + 1}]
                        </span>
                      </div>
                      {result.preview && (
                        <p className="text-xs text-text-secondary line-clamp-2">
                          {result.preview}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-text-muted">
                          {result.type}
                        </span>
                        {result.score && (
                          <span className="text-xs text-accent">
                            {(result.score * 100).toFixed(0)}% match
                          </span>
                        )}
                      </div>
                    </div>
                    <ExternalLink size={14} className="text-text-muted shrink-0 mt-1" />
                  </div>
                </Card>
              ))}
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {!hasSearched && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-center py-16"
          >
            <Search size={48} className="mx-auto text-text-muted mb-4" />
            <p className="text-text-secondary">
              Type a question above to search across your codebase and memories
            </p>
          </motion.div>
        )}
      </div>
    </DashboardShell>
  );
}
