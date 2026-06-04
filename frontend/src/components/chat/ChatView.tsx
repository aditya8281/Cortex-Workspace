import { useEffect, useRef, useState } from "react";
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
                  className="rounded-xl border border-cortex-border bg-cortex-surface/60 p-4 text-left text-sm transition hover:border-cortex-accent/40 hover:bg-cortex-accent-soft"
                  onClick={() => useChatStore.getState().setInputQuery(item.prompt)}
                >
                  <span className="font-medium text-cortex-text">{item.label}</span>
                  <p className="mt-1 text-xs text-cortex-muted line-clamp-2">{item.prompt}</p>
                </button>
              ))}
            </div>
          )}

          {session.messages.map((msg) => (
            <div
              key={msg.id}
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
                ) : streamId === msg.id ? (
                  <StreamingText text={msg.text} animate />
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
                      className="flex items-center gap-1 text-[11px] font-semibold text-cortex-accent hover:underline"
                      onClick={() => setOpenTraces(prev => ({ ...prev, [msg.id]: !prev[msg.id] }))}
                    >
                      {openTraces[msg.id] ? "▼ Hide Agent Trace Details" : "▶ View Agent Collaboration Trace"}
                    </button>
                    
                    {openTraces[msg.id] && (
                      <div className="mt-3.5 space-y-4 rounded-xl border border-cortex-border/60 bg-cortex-elevated/40 p-4.5 text-xs text-cortex-text animate-in fade-in slide-in-from-top-2 duration-200">
                        {/* 1. Summary details */}
                        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4 border-b border-cortex-border/30 pb-3">
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
                          <h4 className="text-[10px] font-bold uppercase tracking-wider text-cortex-muted mb-1.5">Collaboration Graph & Node Timeline</h4>
                          <div className="relative pl-4 border-l border-cortex-border/40 space-y-4">
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
                                <p className="mt-1 text-[11px] text-cortex-muted italic">{node.reasoning_summary}</p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* 3. Verification Report */}
                        {msg.routingInfo.verification_results && (
                          <div className="rounded-lg bg-cortex-surface/40 border border-cortex-border/30 p-3">
                            <h4 className="text-[10px] font-bold uppercase tracking-wider text-cortex-muted mb-2">VerificationAgent Diagnostic Details</h4>
                            <div className="space-y-2">
                              {msg.routingInfo.verification_results.issues.length > 0 ? (
                                <div className="space-y-1.5">
                                  <p className="text-[11px] font-semibold text-red-400">Issues Flagged:</p>
                                  <ul className="list-disc pl-4 text-[11px] text-red-300/90 space-y-0.5">
                                    {msg.routingInfo.verification_results.issues.map((issue, idx) => (
                                      <li key={idx}>{issue}</li>
                                    ))}
                                  </ul>
                                </div>
                              ) : (
                                <p className="text-[11px] font-semibold text-green-400">✅ All validations passed. No hallucinations or invalid file paths detected.</p>
                              )}
                              
                              {/* Raw report preview */}
                              <pre className="mt-2 block max-h-36 overflow-y-auto rounded bg-black/30 p-2 font-mono text-[10px] text-gray-300 whitespace-pre-wrap">
                                {msg.routingInfo.verification_results.report}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
                <div className="mt-2 flex items-center gap-2 text-[10px] opacity-60">
                  <span>{msg.timestamp}</span>
                  {msg.executionId && <Badge variant="accent">trace</Badge>}
                </div>
              </div>
            </div>
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
