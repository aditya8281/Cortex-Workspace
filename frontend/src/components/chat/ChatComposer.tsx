import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { Send, ChevronDown, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/stores/chatStore";
import { useChatSend } from "@/hooks/useChatSend";
import { useQuery } from "@tanstack/react-query";
import { getAllModels } from "@/api/ai";
import { cn } from "@/lib/utils";

export function ChatComposer() {
  const inputQuery = useChatStore((s) => s.inputQuery);
  const setInputQuery = useChatStore((s) => s.setInputQuery);
  const isGenerating = useChatStore((s) => s.isGenerating);
  const activeSession = useChatStore((s) => s.getActiveSession());
  const updateSession = useChatStore((s) => s.updateSession);
  
  const { send } = useChatSend();
  const [local, setLocal] = useState(inputQuery);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch all models
  const { data: models = [] } = useQuery({
    queryKey: ["models"],
    queryFn: getAllModels,
  });

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Determine current active model
  const currentModel = activeSession?.selectedModel || "qwen3:8b";

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

  // Group models
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
      <div className="mx-auto mb-2 flex max-w-3xl items-center justify-between px-1" ref={dropdownRef}>
        <div className="relative">
          <button
            type="button"
            className="flex items-center gap-1.5 rounded-lg border border-cortex-border bg-cortex-elevated/80 px-2.5 py-1.5 text-xs font-semibold text-cortex-text transition hover:border-cortex-accent/40 hover:bg-cortex-accent-soft"
            onClick={() => setOpen(!open)}
          >
            <span className="text-cortex-muted">Model:</span>
            <span className="text-cortex-text">{currentModel}</span>
            <ChevronDown className="h-3 w-3 text-cortex-muted" />
          </button>

          {open && (
            <div className="absolute bottom-full left-0 mb-1.5 z-50 max-h-72 w-72 overflow-y-auto rounded-xl border border-cortex-border bg-cortex-surface/95 p-1.5 shadow-2xl backdrop-blur-lg">
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
                      if (activeSession) {
                        updateSession(activeSession.id, { selectedModel: m.name });
                      }
                      setOpen(false);
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
                      if (activeSession) {
                        updateSession(activeSession.id, { selectedModel: m.name });
                      }
                      setOpen(false);
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
      </div>

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
