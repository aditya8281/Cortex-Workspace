"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Settings, MessageSquare, Trash2 } from "lucide-react";

interface InstalledModel {
  model_id: string;
  display_name: string;
  variant: string;
  size_gb: number;
  last_used: string;
  usage_count: number;
}

interface InstalledBarProps {
  models: InstalledModel[];
  onManage: () => void;
  onChat: (modelId: string) => void;
  onDelete: (modelId: string) => void;
}

export default function InstalledBar({ models, onManage, onChat, onDelete }: InstalledBarProps) {
  const [expanded, setExpanded] = useState(false);
  const totalSize = models.reduce((sum, m) => sum + m.size_gb, 0);

  return (
    <div className="glass-panel rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/[0.02] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] px-2.5 py-0.5 rounded-lg bg-accent/10 text-accent border border-accent/20">
            {models.length} installed
          </span>
          <span className="font-mono text-[11px] text-muted">{totalSize.toFixed(1)} GB</span>
        </div>
        <div className="flex items-center gap-3">
          <span
            role="button"
            tabIndex={0}
            onClick={(e) => { e.stopPropagation(); onManage(); }}
            onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); onManage(); } }}
            className="inline-flex items-center gap-1 text-[11px] text-accent hover:text-accent-bright transition-colors cursor-pointer"
          >
            <Settings size={12} />
            Manage
          </span>
          {expanded ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/[0.06]">
          {models.map((m) => (
            <div key={m.model_id} className="px-4 py-2.5 flex justify-between items-center border-b border-white/[0.06] last:border-b-0 hover:bg-white/[0.02]">
              <div className="min-w-0">
                <div className="text-[12px] font-medium text-primary truncate">{m.display_name} · {m.variant}</div>
                <div className="font-mono text-[10px] text-muted">{m.size_gb} GB · Last used {m.last_used} · {m.usage_count.toLocaleString()} requests</div>
              </div>
              <div className="flex gap-2 ml-3 shrink-0">
                <button
                  onClick={() => onChat(m.model_id)}
                  className="inline-flex items-center gap-1 text-[10px] font-medium px-2.5 py-1 rounded-lg border border-white/[0.08] text-secondary hover:border-accent/40 hover:text-accent transition-all"
                >
                  <MessageSquare size={10} />
                  Chat
                </button>
                <button
                  onClick={() => onDelete(m.model_id)}
                  className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-lg border border-danger/20 text-danger hover:bg-danger/10 hover:border-danger/40 transition-all"
                  aria-label={`Delete ${m.display_name}`}
                >
                  <Trash2 size={10} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
