"use client";

import { useState, useMemo } from "react";
import { Search, MessageSquare, Code, Eye, Sparkles } from "lucide-react";
import type { ModelInfo } from "@/shared/types";

interface CatalogTableProps {
  models: ModelInfo[];
  onDownload: (modelName: string) => void;
}

const TYPE_FILTERS = ["All", "Chat", "Code", "Vision", "Embed"] as const;
const SIZE_FILTERS = ["All", "≤3B", "3-8B", "8-14B", "14B+"] as const;

function matchesSizeFilter(paramCount: string | undefined | null, filter: string): boolean {
  if (filter === "All") return true;
  if (!paramCount) return false;
  const match = paramCount.match(/([\d.]+)B/);
  if (!match) return false;
  const num = parseFloat(match[1]);
  switch (filter) {
    case "≤3B": return num <= 3;
    case "3-8B": return num > 3 && num <= 8;
    case "8-14B": return num > 8 && num <= 14;
    case "14B+": return num > 14;
    default: return true;
  }
}

function formatSize(bytes: number | undefined | null): string {
  if (!bytes) return "—";
  return `${(bytes / 1e9).toFixed(1)} GB`;
}

export default function CatalogTable({ models, onDownload }: CatalogTableProps) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("All");
  const [sizeFilter, setSizeFilter] = useState<string>("All");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 20;

  const filtered = useMemo(() => {
    return models.filter((m) => {
      if (search && !m.display_name.toLowerCase().includes(search.toLowerCase())) return false;
      if (typeFilter !== "All" && m.model_type.toLowerCase() !== typeFilter.toLowerCase()) return false;
      if (!matchesSizeFilter(m.parameter_count, sizeFilter)) return false;
      return true;
    });
  }, [models, search, typeFilter, sizeFilter]);

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="mb-7">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted mb-3 flex items-center gap-2">
        Browse all models
        <span className="flex-1 h-px bg-white/[0.06]" />
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-white/[0.06] flex gap-2 items-center flex-wrap">
          <div className="flex-1 min-w-[200px] relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              placeholder="Search models..."
              className="w-full font-inter text-[13px] pl-9 pr-3 py-2 rounded-lg border border-white/[0.06] bg-surface text-primary outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 placeholder:text-muted transition-all"
            />
          </div>
          {TYPE_FILTERS.map((t) => (
            <button
              key={t}
              onClick={() => { setTypeFilter(t); setPage(0); }}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-lg border transition-all ${
                typeFilter === t
                  ? "border-accent/40 text-accent bg-accent/10 shadow-[0_0_8px_rgba(14,165,201,0.1)]"
                  : "border-white/[0.06] text-muted hover:border-white/[0.12] hover:text-secondary bg-surface/50"
              }`}
            >
              {t}
            </button>
          ))}
          <div className="w-px h-4 bg-white/[0.06] mx-1" />
          {SIZE_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => { setSizeFilter(s); setPage(0); }}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-lg border transition-all ${
                sizeFilter === s
                  ? "border-accent/40 text-accent bg-accent/10 shadow-[0_0_8px_rgba(14,165,201,0.1)]"
                  : "border-white/[0.06] text-muted hover:border-white/[0.12] hover:text-secondary bg-surface/50"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Model</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Type</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Params</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Size</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Fit</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left"></th>
              </tr>
            </thead>
            <tbody>
              {paged.map((m, idx) => (
                <tr key={m.model_id || m.name || idx} className="border-b border-white/[0.06] last:border-b-0 hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-2.5 text-[13px] font-medium text-primary">{m.display_name}</td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded-md ${
                      m.model_type === "chat" ? "bg-accent/10 text-accent" :
                      m.model_type === "code" ? "bg-purple-500/10 text-purple-400" :
                      m.model_type === "vision" ? "bg-warning/10 text-warning" :
                      "bg-white/5 text-secondary"
                    }`}>
                      {m.model_type === "chat" && <MessageSquare size={10} />}
                      {m.model_type === "code" && <Code size={10} />}
                      {m.model_type === "vision" && <Eye size={10} />}
                      {m.model_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-secondary">{m.parameter_count || "—"}</td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-secondary">{formatSize(m.size_bytes)}</td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-muted">—</td>
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => onDownload(m.name)}
                      className="inline-flex items-center gap-1 text-[11px] font-medium px-3 py-1.5 rounded-lg border border-accent/20 text-accent hover:bg-accent/10 hover:border-accent/40 transition-all"
                      aria-label={`Download ${m.display_name}`}
                    >
                      <Sparkles size={12} />
                      Get
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 border-t border-white/[0.06] flex justify-between items-center text-[12px] text-muted">
          <span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length} models</span>
          <div className="flex gap-1">
            {Array.from({ length: Math.min(pageCount, 5) }, (_, i) => (
              <button
                key={i}
                onClick={() => setPage(i)}
                className={`font-mono text-[11px] px-2.5 py-1 rounded-lg border transition-all ${
                  page === i
                    ? "border-accent/40 text-accent bg-accent/10"
                    : "border-white/[0.06] text-secondary hover:border-white/[0.12] hover:text-primary"
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
