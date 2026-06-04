import { useRef, useState } from "react";
import {
  FileText,
  Folder,
  Globe,
  Terminal,
  Brain,
  GitBranch,
  X,
  Upload,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ContextItem, ContextItemKind } from "@/types/cortex";
import { useContextStore } from "@/stores/contextStore";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

// ---------------------------------------------------------------------------
// Tile definitions
// ---------------------------------------------------------------------------

type TileId =
  | "file"
  | "folder"
  | "url"
  | "terminal"
  | "memory"
  | "repo"
  | null;

const TILES: {
  id: Exclude<TileId, null>;
  icon: React.ElementType;
  label: string;
  description: string;
  color: string;
}[] = [
  {
    id: "file",
    icon: FileText,
    label: "Attach File",
    description: "Read any file on disk",
    color: "text-blue-400",
  },
  {
    id: "folder",
    icon: Folder,
    label: "Attach Folder",
    description: "Explore directory tree",
    color: "text-yellow-400",
  },
  {
    id: "url",
    icon: Globe,
    label: "Attach URL",
    description: "Fetch web page content",
    color: "text-green-400",
  },
  {
    id: "terminal",
    icon: Terminal,
    label: "Terminal Output",
    description: "Paste command output",
    color: "text-orange-400",
  },
  {
    id: "memory",
    icon: Brain,
    label: "Attach Memory",
    description: "Select a memory entry",
    color: "text-purple-400",
  },
  {
    id: "repo",
    icon: GitBranch,
    label: "Attach Repository",
    description: "Load repo architecture",
    color: "text-pink-400",
  },
];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ContextAttacherProps {
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ContextAttacher({ onClose }: ContextAttacherProps) {
  const { attach } = useContextStore();
  const [activeFlow, setActiveFlow] = useState<TileId>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  // Shared form state
  const [urlValue, setUrlValue] = useState("");
  const [terminalValue, setTerminalValue] = useState("");
  const [memorySearch, setMemorySearch] = useState("");
  const [selectedMemory, setSelectedMemory] = useState<string | null>(null);
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);

  // Fetch memory entries for picker
  const { data: memoryEntries = [] } = useQuery({
    queryKey: ["memory-entries"],
    queryFn: async () => {
      const res = await api.get("/intelligence/knowledge", { params: { limit: 50 } });
      return (res.data as { id: number; title: string; summary?: string }[]) ?? [];
    },
    enabled: activeFlow === "memory",
  });

  // Fetch repo profiles for picker
  const { data: repositories = [] } = useQuery({
    queryKey: ["repo-profiles"],
    queryFn: async () => {
      const res = await api.get("/intelligence/repositories");
      return (res.data as { name: string; path?: string }[]) ?? [];
    },
    enabled: activeFlow === "repo",
  });

  // -------------------------------------------------------------------------
  // Attach helpers
  // -------------------------------------------------------------------------

  const attachItem = (item: ContextItem) => {
    attach(item);
    onClose();
  };

  const makeId = () => `ctx-${crypto.randomUUID()}`;

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text().catch(() => "");
    attachItem({
      id: makeId(),
      kind: "file",
      title: file.name,
      path: (file as File & { path?: string }).path || file.name,
      contentPreview: text.slice(0, 500),
    });
  };

  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const first = files[0] as File & { webkitRelativePath?: string };
    const folderName = first.webkitRelativePath?.split("/")[0] ?? "Folder";
    const fileList = Array.from(files)
      .slice(0, 20)
      .map((f) => `  ${(f as File & { webkitRelativePath?: string }).webkitRelativePath ?? f.name}`)
      .join("\n");
    attachItem({
      id: makeId(),
      kind: "folder",
      title: folderName,
      contentPreview: `${files.length} files\n${fileList}`,
    });
  };

  const handleAttachUrl = () => {
    const trimmed = urlValue.trim();
    if (!trimmed) return;
    attachItem({ id: makeId(), kind: "url", title: trimmed, url: trimmed });
  };

  const handleAttachTerminal = () => {
    if (!terminalValue.trim()) return;
    attachItem({
      id: makeId(),
      kind: "terminal",
      title: "Terminal Output",
      contentPreview: terminalValue.trim(),
    });
  };

  const handleAttachMemory = () => {
    const entry = memoryEntries.find((m) => String(m.id) === selectedMemory);
    if (!entry) return;
    attachItem({
      id: makeId(),
      kind: "memory",
      title: entry.title,
      detail: entry.summary,
    });
  };

  const handleAttachRepo = () => {
    const repo = repositories.find((r) => r.name === selectedRepo);
    if (!repo) return;
    attachItem({
      id: makeId(),
      kind: "repo",
      title: repo.name,
      path: repo.path,
    });
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  const filteredMemory = memoryEntries.filter((m) =>
    m.title.toLowerCase().includes(memorySearch.toLowerCase())
  );

  return (
    <div className="rounded-2xl border border-cortex-border bg-cortex-surface/98 shadow-2xl backdrop-blur-xl w-80 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-cortex-border/60 px-4 py-3">
        <span className="text-xs font-bold tracking-wider text-cortex-text uppercase">
          {activeFlow ? TILES.find((t) => t.id === activeFlow)?.label : "Add Context"}
        </span>
        <button
          type="button"
          className="rounded-md p-1 text-cortex-muted hover:text-cortex-text transition-colors"
          onClick={activeFlow ? () => setActiveFlow(null) : onClose}
        >
          {activeFlow ? (
            <ChevronRight className="h-3.5 w-3.5 rotate-180" />
          ) : (
            <X className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      {/* Tile grid */}
      {!activeFlow && (
        <div className="grid grid-cols-2 gap-1.5 p-3">
          {TILES.map((tile) => (
            <button
              key={tile.id}
              type="button"
              className="flex flex-col items-start gap-1.5 rounded-xl border border-cortex-border/50 bg-cortex-elevated/60 p-3 text-left transition-all duration-150 hover:border-cortex-accent/40 hover:bg-cortex-accent-soft hover:shadow-sm"
              onClick={() => {
                if (tile.id === "file") {
                  fileInputRef.current?.click();
                } else if (tile.id === "folder") {
                  folderInputRef.current?.click();
                } else {
                  setActiveFlow(tile.id);
                }
              }}
            >
              <tile.icon className={cn("h-4 w-4", tile.color)} />
              <div>
                <p className="text-[11px] font-semibold text-cortex-text">{tile.label}</p>
                <p className="text-[9px] text-cortex-muted leading-tight">{tile.description}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Hidden file inputs */}
      <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelect} />
      <input
        ref={folderInputRef}
        type="file"
        className="hidden"
        // @ts-ignore – webkitdirectory is not in React's HTMLInputElement types
        webkitdirectory=""
        multiple
        onChange={handleFolderSelect}
      />

      {/* ------------------------------------------------------------------ */}
      {/* Flow: URL */}
      {/* ------------------------------------------------------------------ */}
      {activeFlow === "url" && (
        <div className="p-4 space-y-3">
          <label className="text-[10px] font-medium text-cortex-muted uppercase tracking-wider">
            URL
          </label>
          <input
            autoFocus
            type="url"
            value={urlValue}
            onChange={(e) => setUrlValue(e.target.value)}
            placeholder="https://example.com/docs"
            className="w-full rounded-lg border border-cortex-border bg-cortex-elevated px-3 py-2 text-sm text-cortex-text placeholder:text-cortex-muted focus:outline-none focus:ring-2 focus:ring-cortex-accent/30"
            onKeyDown={(e) => e.key === "Enter" && handleAttachUrl()}
          />
          <button
            type="button"
            disabled={!urlValue.trim()}
            onClick={handleAttachUrl}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-cortex-accent px-3 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            <Upload className="h-3.5 w-3.5" />
            Attach URL
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Flow: Terminal */}
      {/* ------------------------------------------------------------------ */}
      {activeFlow === "terminal" && (
        <div className="p-4 space-y-3">
          <label className="text-[10px] font-medium text-cortex-muted uppercase tracking-wider">
            Paste terminal output
          </label>
          <textarea
            autoFocus
            value={terminalValue}
            onChange={(e) => setTerminalValue(e.target.value)}
            rows={6}
            placeholder="$ npm run build&#10;> Error: ..."
            className="w-full rounded-lg border border-cortex-border bg-cortex-elevated px-3 py-2 font-mono text-xs text-cortex-text placeholder:text-cortex-muted focus:outline-none focus:ring-2 focus:ring-cortex-accent/30 resize-none"
          />
          <button
            type="button"
            disabled={!terminalValue.trim()}
            onClick={handleAttachTerminal}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-cortex-accent px-3 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            <Terminal className="h-3.5 w-3.5" />
            Attach Output
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Flow: Memory */}
      {/* ------------------------------------------------------------------ */}
      {activeFlow === "memory" && (
        <div className="p-4 space-y-3">
          <label className="text-[10px] font-medium text-cortex-muted uppercase tracking-wider">
            Search memory
          </label>
          <input
            autoFocus
            value={memorySearch}
            onChange={(e) => setMemorySearch(e.target.value)}
            placeholder="PLDNet, RLHF notes…"
            className="w-full rounded-lg border border-cortex-border bg-cortex-elevated px-3 py-2 text-sm text-cortex-text placeholder:text-cortex-muted focus:outline-none focus:ring-2 focus:ring-cortex-accent/30"
          />
          <div className="max-h-40 overflow-y-auto space-y-1">
            {filteredMemory.length === 0 && (
              <p className="text-xs text-cortex-muted italic py-2 text-center">
                No entries found
              </p>
            )}
            {filteredMemory.map((entry) => (
              <button
                key={entry.id}
                type="button"
                onClick={() => setSelectedMemory(String(entry.id))}
                className={cn(
                  "w-full rounded-lg px-3 py-2 text-left text-xs transition hover:bg-cortex-accent-soft",
                  selectedMemory === String(entry.id)
                    ? "bg-cortex-accent-soft text-cortex-accent font-semibold border border-cortex-accent/30"
                    : "text-cortex-text border border-transparent"
                )}
              >
                {entry.title}
                {entry.summary && (
                  <span className="block text-[10px] text-cortex-muted truncate">
                    {entry.summary}
                  </span>
                )}
              </button>
            ))}
          </div>
          <button
            type="button"
            disabled={!selectedMemory}
            onClick={handleAttachMemory}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-cortex-accent px-3 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            <Brain className="h-3.5 w-3.5" />
            Attach Memory
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Flow: Repository */}
      {/* ------------------------------------------------------------------ */}
      {activeFlow === "repo" && (
        <div className="p-4 space-y-3">
          <label className="text-[10px] font-medium text-cortex-muted uppercase tracking-wider">
            Select repository
          </label>
          <div className="max-h-48 overflow-y-auto space-y-1">
            {repositories.length === 0 && (
              <p className="text-xs text-cortex-muted italic py-2 text-center">
                No repositories indexed yet
              </p>
            )}
            {repositories.map((repo) => (
              <button
                key={repo.name}
                type="button"
                onClick={() => setSelectedRepo(repo.name)}
                className={cn(
                  "w-full rounded-lg px-3 py-2 text-left text-xs transition hover:bg-cortex-accent-soft",
                  selectedRepo === repo.name
                    ? "bg-cortex-accent-soft text-cortex-accent font-semibold border border-cortex-accent/30"
                    : "text-cortex-text border border-transparent"
                )}
              >
                <span className="font-mono">{repo.name}</span>
                {repo.path && (
                  <span className="block text-[10px] text-cortex-muted truncate">{repo.path}</span>
                )}
              </button>
            ))}
          </div>
          <button
            type="button"
            disabled={!selectedRepo}
            onClick={handleAttachRepo}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-cortex-accent px-3 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            <GitBranch className="h-3.5 w-3.5" />
            Attach Repository
          </button>
        </div>
      )}
    </div>
  );
}
