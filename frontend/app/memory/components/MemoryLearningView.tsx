"use client";

import { TrendingUp, Trash2, Sparkles } from "lucide-react";
import type { LongTermMemory, MemoryStats } from "../../../src/shared/types";
import { cn } from "../../../src/lib/utils";

const categoryColors: Record<string, string> = {
  code: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  document: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  note: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  idea: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  default: "bg-accent/10 text-accent border-accent/20",
};

interface LearningViewProps {
  stats: MemoryStats | null;
  memories: Record<string, LongTermMemory[]>;
  loading: boolean;
  onReinforce: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function LearningView({ stats, memories, loading, onReinforce, onDelete }: LearningViewProps) {
  if (loading && !stats) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-bg-elevated border border-border-subtle" />
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex flex-col items-center py-12 text-center">
        <Sparkles className="h-12 w-12 text-accent/30 mb-3" />
        <p className="text-sm font-medium text-text mb-1">No learned memories yet</p>
        <p className="text-xs text-text-muted max-w-xs">
          Cortex will automatically extract insights from your conversations.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
          <p className="text-xs text-text-muted mb-1">Total Memories</p>
          <p className="text-2xl font-bold text-text">{stats.total}</p>
        </div>
        <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
          <p className="text-xs text-text-muted mb-1">Active</p>
          <p className="text-2xl font-bold text-success">{stats.active}</p>
        </div>
        <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
          <p className="text-xs text-text-muted mb-1">Avg Confidence</p>
          <p className="text-2xl font-bold text-accent">{(stats.avg_confidence * 100).toFixed(0)}%</p>
        </div>
        <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
          <p className="text-xs text-text-muted mb-1">Categories</p>
          <p className="text-2xl font-bold text-text">{Object.keys(stats.by_category).length}</p>
        </div>
      </div>

      <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
        <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-accent" />
          By Category
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Object.entries(stats.by_category).map(([cat, count]) => (
            <div key={cat} className="flex items-center justify-between rounded-lg bg-bg-surface px-3 py-2 border border-border-subtle">
              <span className="text-xs font-medium text-text capitalize">{cat}</span>
              <span className="text-xs font-mono text-text-muted">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {Object.entries(memories).map(([cat, catMemories]) =>
        catMemories.length > 0 ? (
          <div key={cat} className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
            <h3 className="text-sm font-semibold text-text mb-3 capitalize flex items-center gap-2">
              <span className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider border",
                categoryColors[cat] || categoryColors.default
              )}>
                {cat}
              </span>
              <span className="text-xs text-text-muted font-normal">({catMemories.length})</span>
            </h3>
            <div className="space-y-2">
              {catMemories.map((m) => (
                <div key={m.id} className="flex items-start gap-3 rounded-lg bg-bg-surface p-3 border border-border-subtle">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-text truncate">{m.title}</p>
                    <p className="text-[11px] text-text-muted mt-0.5 line-clamp-2">{m.content}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <div className="flex-1 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                        <div className="h-full bg-accent rounded-full transition-all" style={{ width: `${m.confidence * 100}%` }} />
                      </div>
                      <span className="text-[10px] font-mono text-text-muted shrink-0">
                        {(m.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1 shrink-0">
                    <button onClick={() => onReinforce(m.id)}
                      className="text-[10px] text-accent hover:text-accent/80 transition-colors px-1.5 py-0.5 rounded hover:bg-accent/10"
                      title="Reinforce">
                      <TrendingUp className="h-3 w-3" />
                    </button>
                    <button onClick={() => onDelete(m.id)}
                      className="text-[10px] text-error/60 hover:text-error transition-colors px-1.5 py-0.5 rounded hover:bg-error/10"
                      title="Delete">
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null
      )}

      {Object.values(memories).every((m) => m.length === 0) && (
        <div className="flex flex-col items-center py-12 text-center">
          <Sparkles className="h-12 w-12 text-accent/30 mb-3" />
          <p className="text-sm font-medium text-text mb-1">No learned memories yet</p>
          <p className="text-xs text-text-muted max-w-xs">
            Cortex will automatically extract insights from your conversations.
          </p>
        </div>
      )}
    </div>
  );
}
