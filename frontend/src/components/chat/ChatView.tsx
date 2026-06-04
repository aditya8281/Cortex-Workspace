import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MarkdownMessage } from "./MarkdownMessage";
import { StreamingText } from "./StreamingText";
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
  const [streamId, setStreamId] = useState<string | null>(null);
  const prevCount = useRef(0);
  const [openTraces, setOpenTraces] = useState<Record<string, boolean>>({});

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages.length, isGenerating]);

  useEffect(() => {
    const count = session?.messages.length ?? 0;
    if (count > prevCount.current && session) {
      const last = session.messages[session.messages.length - 1];
      if (last?.sender === "assistant" && last.id !== "welcome") {
        setStreamId(last.id);
      }
    }
    prevCount.current = count;
  }, [session?.messages.length, session]);

  if (!session) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-cortex-muted">
        Loading chat…
      </div>
    );
  }

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
                  className="rounded-2xl border border-cortex-border/80 bg-cortex-surface/65 p-4 text-left text-sm shadow-sm transition duration-200 ease-out hover:-translate-y-0.5 hover:border-cortex-accent/30 hover:bg-cortex-accent-soft"
                  onClick={() => useChatStore.getState().setInputQuery(item.prompt)}
                >
                  <span className="font-medium text-cortex-text">{item.label}</span>
                  <p className="mt-1 text-xs text-cortex-muted line-clamp-2">{item.prompt}</p>
                </button>
              ))}
            </div>
          )}

          <AnimatePresence initial={false}>
            {session.messages.map((msg) => (
              <motion.div
                key={msg.id}
                layout
                initial={{ opacity: 0, x: msg.sender === "user" ? 18 : -18, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, x: 0, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22, ease: "easeOut" }}
                className={cn("flex gap-3", msg.sender === "user" ? "justify-end" : "justify-start")}
              >
                {msg.sender === "assistant" && (
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-cortex-border/60 bg-gradient-to-br from-cortex-accent-soft via-cortex-surface to-cortex-elevated text-xs font-bold text-cortex-accent shadow-sm">
                    C
                  </div>
                )}
                <div
                  className={cn(
                    "max-w-[85%] rounded-3xl px-4 py-3 shadow-sm backdrop-blur-sm",
                    msg.sender === "user"
                      ? "bg-gradient-to-br from-cortex-accent via-sky-500 to-cyan-500 text-white shadow-[0_18px_45px_rgba(109,156,255,0.22)]"
                      : "border border-cortex-border/70 bg-cortex-surface/80",
                  )}
                >
                  {msg.sender === "user" ? (
                    <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                  ) : streamId === msg.id ? (
                    <div className="space-y-2">
                      <StreamingText text={msg.text} animate />
                      <div className="flex items-center gap-1.5 text-cortex-muted">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cortex-accent" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cortex-accent [animation-delay:140ms]" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cortex-accent [animation-delay:280ms]" />
                      </div>
                    </div>
                  ) : (
                    <MarkdownMessage content={msg.text} />
                  )}
                  {msg.routingInfo && (
                    <div className="mt-2.5 flex flex-wrap items-center gap-2 border-t border-cortex-border/40 pt-2 text-[10px] text-cortex-muted">
                      <Badge variant="accent" className="text-[9px] py-0.5 px-1.5 shrink-0">
                        {msg.routingInfo.model_used}
                      </Badge>
                      <span className="shrink-0 font-medium text-cortex-text">{msg.routingInfo.provider}</span>
                      <span className="shrink-0 opacity-40">|</span>
                      <span className="shrink-0 font-medium text-cortex-accent">{msg.routingInfo.response_time.toFixed(2)}s</span>

                      {msg.routingInfo.agent_selected && (
                        <>
                          <span className="shrink-0 opacity-40">|</span>
                          <span className="shrink-0 font-semibold text-purple-400">🤖 {msg.routingInfo.agent_selected}</span>
                          <span className="shrink-0 text-cortex-muted">({((msg.routingInfo.agent_confidence ?? 0) * 100).toFixed(0)}% conf)</span>
                          {msg.routingInfo.agent_execution_time !== undefined && (
                            <span className="shrink-0 font-medium text-purple-300">in {msg.routingInfo.agent_execution_time.toFixed(2)}s</span>
                          )}
                        </>
                      )}

                      <span className="shrink-0 opacity-40">|</span>
                      <span className="italic truncate max-w-[200px] sm:max-w-[300px]" title={msg.routingInfo.agent_reason || msg.routingInfo.selection_reason}>
                        {msg.routingInfo.agent_reason || msg.routingInfo.selection_reason}
                      </span>
                    </div>
                  )}
                  {msg.routingInfo && msg.routingInfo.collaboration_graph && (
                    <div className="mt-3 border-t border-cortex-border/30 pt-2.5">
                      <button
                        type="button"
                        className="flex items-center gap-1 text-[11px] font-semibold text-cortex-accent transition hover:opacity-80"
                        onClick={() => setOpenTraces(prev => ({ ...prev, [msg.id]: !prev[msg.id] }))}
                      >
                        {openTraces[msg.id] ? "▼ Hide Agent Trace Details" : "▶ View Agent Collaboration Trace"}
                      </button>

                      {openTraces[msg.id] && (
                        <motion.div
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -6 }}
                          transition={{ duration: 0.2, ease: "easeOut" }}
                          className="mt-3.5 space-y-4 rounded-2xl border border-cortex-border/60 bg-cortex-elevated/45 p-4 text-xs text-cortex-text"
                        >
                          <div className="grid grid-cols-2 gap-3.5 border-b border-cortex-border/30 pb-3 sm:grid-cols-4">
                          <div>
                            <span className="block text-[10px] uppercase font-bold text-cortex-muted">Task Class</span>
                            <span className="font-semibold text-purple-400">{msg.routingInfo.classified_task || "Chat"}</span>
                          </div>
                          <div>
                            <span className="block text-[10px] uppercase font-bold text-cortex-muted">Execution Order</span>
                            <span className="font-mono text-[10px] text-cortex-text truncate block" title={msg.routingInfo.execution_order?.join(" → ")}>
                              {msg.routingInfo.execution_order?.join(" → ") || "None"}
                            </span>
                          </div>
                          <div>
                            <span className="block text-[10px] uppercase font-bold text-cortex-muted">Duration</span>
                            <span className="font-semibold text-cortex-accent">{msg.routingInfo.agent_execution_time?.toFixed(2) || msg.routingInfo.response_time.toFixed(2)}s</span>
                          </div>
                          <div>
                            <span className="block text-[10px] uppercase font-bold text-cortex-muted">Verification</span>
                            {msg.routingInfo.verification_results ? (
                              <span className={cn(
                                "inline-flex rounded-full px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide",
                                msg.routingInfo.verification_results.verified
                                  ? "bg-green-500/15 text-green-400 border border-green-500/30"
                                  : "bg-red-500/15 text-red-400 border border-red-500/30"
                              )}>
                                {msg.routingInfo.verification_results.verified ? "Passed" : "Failed"}
                              </span>
                            ) : (
                              <span className="text-cortex-muted">N/A</span>
                            )}
                          </div>
                        </div>

                        {/* 2. Collaboration graph nodes */}
                          <div className="space-y-3">
                            <h4 className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-cortex-muted">Collaboration Graph & Node Timeline</h4>
                            <div className="relative space-y-4 border-l border-cortex-border/40 pl-4">
                              {msg.routingInfo.collaboration_graph.map((node) => (
                                <div key={node.id} className="relative">
                                {/* Dot indicator */}
                                <span className={cn(
                                  "absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-cortex-surface",
                                  node.status === "completed" ? "bg-green-500" :
                                  node.status === "running" ? "bg-blue-500" :
                                  node.status === "failed" ? "bg-red-500" : "bg-gray-500"
                                )} />
                                
                                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-1">
                                  <div>
                                    <span className="font-semibold text-purple-300">🤖 {node.agent_name}</span>
                                    {node.depends_on.length > 0 && (
                                      <span className="ml-2 text-[10px] font-normal text-cortex-muted">
                                        (depends on: {node.depends_on.join(", ")})
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-2 text-[10px] text-cortex-muted shrink-0">
                                    <span>{node.execution_time.toFixed(3)}s</span>
                                    <span>•</span>
                                    <span>{(node.confidence * 100).toFixed(0)}% conf</span>
                                  </div>
                                </div>
                                  <p className="mt-1 text-[11px] italic text-cortex-muted">{node.reasoning_summary}</p>
                                </div>
                              ))}
                            </div>
                          </div>

                          {msg.routingInfo.verification_results && (
                            <div className="rounded-xl border border-cortex-border/30 bg-cortex-surface/40 p-3">
                              <h4 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-cortex-muted">VerificationAgent Diagnostic Details</h4>
                              <div className="space-y-2">
                                {msg.routingInfo.verification_results.issues.length > 0 ? (
                                  <div className="space-y-1.5">
                                    <p className="text-[11px] font-semibold text-red-400">Issues Flagged:</p>
                                    <ul className="list-disc space-y-0.5 pl-4 text-[11px] text-red-300/90">
                                      {msg.routingInfo.verification_results.issues.map((issue, idx) => (
                                        <li key={idx}>{issue}</li>
                                      ))}
                                    </ul>
                                  </div>
                                ) : (
                                  <p className="text-[11px] font-semibold text-green-400">✅ All validations passed. No hallucinations or invalid file paths detected.</p>
                                )}

                                <pre className="mt-2 block max-h-36 overflow-y-auto rounded-lg bg-black/30 p-2 font-mono text-[10px] text-gray-300 whitespace-pre-wrap">
                                  {msg.routingInfo.verification_results.report}
                                </pre>
                              </div>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </div>
                  )}
                  <div className="mt-2 flex items-center gap-2 text-[10px] opacity-60">
                    <span>{msg.timestamp}</span>
                    {msg.executionId && <Badge variant="accent">trace</Badge>}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

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
