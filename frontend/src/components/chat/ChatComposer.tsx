import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { Send, ChevronDown, Check, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/stores/chatStore";
import { useChatSend } from "@/hooks/useChatSend";
import { useQuery } from "@tanstack/react-query";
import { getAllModels } from "@/api/ai";
import { cn } from "@/lib/utils";
import { useContextStore } from "@/stores/contextStore";
import { ContextAttacher } from "@/components/chat/ContextAttacher";

// Kind → accent colour mapping for chips
const KIND_COLORS: Record<string, string> = {
  file: "bg-blue-500/15 border-blue-400/30 text-blue-300",
  folder: "bg-yellow-500/15 border-yellow-400/30 text-yellow-300",
  url: "bg-green-500/15 border-green-400/30 text-green-300",
  terminal: "bg-orange-500/15 border-orange-400/30 text-orange-300",
  memory: "bg-purple-500/15 border-purple-400/30 text-purple-300",
  repo: "bg-pink-500/15 border-pink-400/30 text-pink-300",
  activity: "bg-cortex-accent/15 border-cortex-accent/30 text-cortex-accent",
};

const KIND_EMOJI: Record<string, string> = {
  file: "📄",
  folder: "📁",
  url: "🔗",
  terminal: "💻",
  memory: "🧠",
  repo: "📦",
  activity: "⚡",
};

export function ChatComposer() {
  const inputQuery = useChatStore((s) => s.inputQuery);
  const setInputQuery = useChatStore((s) => s.setInputQuery);
  const isGenerating = useChatStore((s) => s.isGenerating);
  const activeSession = useChatStore((s) => s.getActiveSession());
  const updateSession = useChatStore((s) => s.updateSession);

  const { list: listContext, remove: removeContext } = useContextStore();

  const { send } = useChatSend();
  const [local, setLocal] = useState(inputQuery);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [attacherOpen, setAttacherOpen] = useState(false);
  const modelDropdownRef = useRef<HTMLDivElement>(null);
  const attacherRef = useRef<HTMLDivElement>(null);

  // Fetch all models for model selector
  const { data: models = [] } = useQuery({
    queryKey: ["models"],
    queryFn: getAllModels,
  });

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target as Node)) {
        setModelDropdownOpen(false);
      }
      if (attacherRef.current && !attacherRef.current.contains(event.target as Node)) {
        setAttacherOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const currentModel = activeSession?.selectedModel || "Auto";
  const contextItems = listContext();

  const submit = async (text?: string) => {
    const q = (text ?? local).trim();
    if (!q || isGenerating) return;
    setLocal("");
    setInputQuery("");
    await send(q);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  };

  const localModels = models.filter((m) => m.is_local);
  const cloudModels = models.filter((m) => !m.is_local);

  return (
    <form
      className="border-t border-cortex-border bg-cortex-surface/90 p-4 backdrop-blur-md"
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        void submit();
      }}
    >
      {/* ------------------------------------------------------------------ */}
      {/* Context chips — appear above the input when items are attached      */}
      {/* ------------------------------------------------------------------ */}
      {contextItems.length > 0 && (
        <div className="mx-auto mb-2.5 flex max-w-3xl flex-wrap gap-1.5 px-1">
          {contextItems.map((item) => {
            const colorClass = KIND_COLORS[item.kind] ?? "bg-cortex-elevated border-cortex-border text-cortex-text";
            const emoji = KIND_EMOJI[item.kind] ?? "📎";
            return (
              <span
                key={item.id}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-all",
                  colorClass
                )}
              >
                <span>{emoji}</span>
                <span className="max-w-[120px] truncate">{item.title}</span>
                <button
                  type="button"
                  className="ml-0.5 rounded-full p-0.5 opacity-60 hover:opacity-100 transition-opacity"
                  onClick={() => removeContext(item.id)}
                  aria-label={`Remove ${item.title}`}
                >
                  <X className="h-2.5 w-2.5" />
                </button>
              </span>
            );
          })}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Toolbar row: model selector + attach button                         */}
      {/* ------------------------------------------------------------------ */}
      <div className="mx-auto mb-2 flex max-w-3xl items-center gap-2 px-1">
        {/* Model selector */}
        <div className="relative" ref={modelDropdownRef}>
          <button
            type="button"
            className="flex items-center gap-1.5 rounded-lg border border-cortex-border bg-cortex-elevated/80 px-2.5 py-1.5 text-xs font-semibold text-cortex-text transition hover:border-cortex-accent/40 hover:bg-cortex-accent-soft"
            onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
          >
            <span className="text-cortex-muted">Model:</span>
            <span className="text-cortex-text">{currentModel}</span>
            <ChevronDown className="h-3 w-3 text-cortex-muted" />
          </button>

          {modelDropdownOpen && (
            <div className="absolute bottom-full left-0 mb-1.5 z-50 max-h-72 w-72 overflow-y-auto rounded-xl border border-cortex-border bg-cortex-surface/95 p-1.5 shadow-2xl backdrop-blur-lg">
              <button
                type="button"
                className={cn(
                  "flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-xs transition-colors hover:bg-white/5",
                  currentModel === "Auto" && "bg-cortex-accent-soft text-cortex-accent"
                )}
                onClick={() => {
                  if (activeSession) updateSession(activeSession.id, { selectedModel: "Auto" });
                  setModelDropdownOpen(false);
                }}
              >
                <div className="flex flex-col">
                  <span className="font-semibold text-cortex-text">Auto Mode</span>
                  <span className="text-[10px] text-cortex-muted">Dynamic model routing based on task</span>
                </div>
                {currentModel === "Auto" && <Check className="h-3.5 w-3.5" />}
              </button>
              <div className="my-1 border-t border-cortex-border/50" />

              <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-cortex-muted">
                Local Models
              </div>
              {localModels.length === 0 ? (
                <div className="px-3 py-1.5 text-xs text-cortex-muted italic">No local models found</div>
              ) : (
                localModels.map((m) => (
                  <button
                    key={m.name}
                    type="button"
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-xs transition hover:bg-white/5",
                      currentModel === m.name ? "text-cortex-accent font-medium bg-cortex-accent-soft" : "text-cortex-text"
                    )}
                    onClick={() => {
                      if (activeSession) updateSession(activeSession.id, { selectedModel: m.name });
                      setModelDropdownOpen(false);
                    }}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate">{m.name}</p>
                      <p className="text-[9px] text-cortex-muted">{m.provider}</p>
                    </div>
                    {currentModel === m.name && <Check className="h-3.5 w-3.5 shrink-0 text-cortex-accent" />}
                  </button>
                ))
              )}

              <div className="my-1.5 border-t border-cortex-border" />
              <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-cortex-muted">
                Cloud Models
              </div>
              {cloudModels.length === 0 ? (
                <div className="px-3 py-1.5 text-xs text-cortex-muted italic">No cloud providers enabled</div>
              ) : (
                cloudModels.map((m) => (
                  <button
                    key={m.name}
                    type="button"
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-xs transition hover:bg-white/5",
                      currentModel === m.name ? "text-cortex-accent font-medium bg-cortex-accent-soft" : "text-cortex-text"
                    )}
                    onClick={() => {
                      if (activeSession) updateSession(activeSession.id, { selectedModel: m.name });
                      setModelDropdownOpen(false);
                    }}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate">{m.name}</p>
                      <p className="text-[9px] text-cortex-muted">{m.provider}</p>
                    </div>
                    {currentModel === m.name && <Check className="h-3.5 w-3.5 shrink-0 text-cortex-accent" />}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Attach context button */}
        <div className="relative" ref={attacherRef}>
          <button
            type="button"
            className={cn(
              "flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition",
              attacherOpen
                ? "border-cortex-accent/50 bg-cortex-accent-soft text-cortex-accent"
                : "border-cortex-border bg-cortex-elevated/80 text-cortex-muted hover:border-cortex-accent/40 hover:bg-cortex-accent-soft hover:text-cortex-text"
            )}
            onClick={() => setAttacherOpen(!attacherOpen)}
          >
            <Plus className="h-3 w-3" />
            <span>Context</span>
            {contextItems.length > 0 && (
              <span className="ml-0.5 rounded-full bg-cortex-accent px-1.5 py-0.5 text-[9px] font-bold text-white">
                {contextItems.length}
              </span>
            )}
          </button>

          {attacherOpen && (
            <div className="absolute bottom-full left-0 mb-1.5 z-50">
              <ContextAttacher onClose={() => setAttacherOpen(false)} />
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Input row                                                            */}
      {/* ------------------------------------------------------------------ */}
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-xl border border-cortex-border bg-cortex-elevated p-2 shadow-sm">
        <textarea
          value={local}
          onChange={(e) => setLocal(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder="Ask Cortex about your machine, repos, or memory…"
          className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2.5 text-sm text-cortex-text placeholder:text-cortex-muted focus:outline-none"
        />
        <Button type="submit" size="icon" disabled={isGenerating || !local.trim()} aria-label="Send">
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-cortex-muted">
        Cortex reads your environment automatically. Modifications require approval.
      </p>
    </form>
  );
}