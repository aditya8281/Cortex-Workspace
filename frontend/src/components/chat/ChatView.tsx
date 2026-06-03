import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { MarkdownMessage } from "./MarkdownMessage";
import { ChatComposer } from "./ChatComposer";
import { useChatStore } from "@/stores/chatStore";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const QUICK = [
  { label: "Sync status", prompt: "What did Cortex learn in the last sync?" },
  { label: "Architecture", prompt: "Summarize the architecture of this workspace" },
  { label: "Find files", prompt: "Find implementation details for the sync service" },
  { label: "System scan", prompt: "Scan the project for risks and mismatches" },
];

export function ChatView() {
  const session = useChatStore((s) => s.getActiveSession());
  const isGenerating = useChatStore((s) => s.isGenerating);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages.length, isGenerating]);

  if (!session) return null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {session.messages.length <= 1 && (
            <div className="grid gap-2 sm:grid-cols-2">
              {QUICK.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  className="rounded-xl border border-cortex-border bg-cortex-surface/60 p-4 text-left text-sm transition hover:border-cortex-accent/40 hover:bg-cortex-accent-soft"
                  onClick={() => useChatStore.getState().setInputQuery(item.prompt)}
                >
                  <span className="font-medium">{item.label}</span>
                  <p className="mt-1 text-xs text-cortex-muted line-clamp-2">{item.prompt}</p>
                </button>
              ))}
            </div>
          )}

          {session.messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("flex gap-3", msg.sender === "user" ? "justify-end" : "justify-start")}
            >
              {msg.sender === "assistant" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cortex-accent-soft text-xs font-bold text-cortex-accent">
                  C
                </div>
              )}
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-4 py-3",
                  msg.sender === "user"
                    ? "bg-cortex-accent text-white"
                    : "border border-cortex-border bg-cortex-surface",
                )}
              >
                {msg.sender === "user" ? (
                  <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                ) : (
                  <MarkdownMessage content={msg.text} />
                )}
                <div className="mt-2 flex items-center gap-2 text-[10px] opacity-60">
                  <span>{msg.timestamp}</span>
                  {msg.executionId && <Badge variant="accent">trace</Badge>}
                </div>
              </div>
            </motion.div>
          ))}

          {isGenerating && (
            <div className="flex items-center gap-2 text-sm text-cortex-muted">
              <span className="inline-flex gap-1">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cortex-accent" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cortex-accent [animation-delay:150ms]" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cortex-accent [animation-delay:300ms]" />
              </span>
              Cortex is thinking…
            </div>
          )}
          <div ref={endRef} />
        </div>
      </div>
      <ChatComposer />
    </div>
  );
}
