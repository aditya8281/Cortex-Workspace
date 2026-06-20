"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, ChevronDown, ChevronUp, Clock, Play, CheckCircle, XCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../src/lib/utils";
import type { Agent, AgentRun, AgentStep } from "../../src/shared/types";
import { agentApi } from "../../src/shared/api/agent";

interface AgentChatProps {
  agent: Agent;
  onRunComplete?: (run: AgentRun) => void;
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  steps?: AgentStep[];
  timestamp?: string;
}

const stepStatusIcons: Record<string, typeof Clock> = {
  pending: Clock,
  running: Play,
  completed: CheckCircle,
  failed: XCircle,
};

const stepStatusColors: Record<string, string> = {
  pending: "text-text-muted",
  running: "text-accent",
  completed: "text-success",
  failed: "text-error",
};

const stepStatusBg: Record<string, string> = {
  pending: "bg-bg-surface text-text-muted",
  running: "bg-accent/10 text-accent",
  completed: "bg-success/10 text-success",
  failed: "bg-error/10 text-error",
};

export default function AgentChat({ agent, onRunComplete }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function toggleStep(key: string) {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const result = await agentApi.run({ agent_id: agent.id, input: userMessage.content });
      const runId = result.run_id;

      // Poll for completion
      let runData: { run: AgentRun; steps: AgentStep[] } | null = null;
      for (let attempts = 0; attempts < 120; attempts++) {
        await new Promise((r) => setTimeout(r, 2000));
        const statusRes = await agentApi.getRunStatus(runId);
        if (statusRes.status === "completed" || statusRes.status === "failed" || statusRes.status === "unknown") {
          // Fetch full run details
          runData = await agentApi.getRun(runId);
          break;
        }
      }

      if (!runData) {
        throw new Error("Timed out waiting for agent run");
      }

      const run = runData.run;
      const steps = runData.steps || [];

      const assistantMessage: Message = {
        role: "assistant",
        content: run.output || run.error || "No output",
        steps,
        timestamp: run.completed_at || undefined,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      onRunComplete?.(run);
    } catch (err) {
      const errorMessage: Message = {
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="h-12 w-12 text-accent/30 mb-3" />
            <p className="text-sm text-text-muted">
              Chat with <span className="font-medium text-text">{agent.name}</span>
            </p>
            <p className="text-xs text-text-muted/60 mt-1 max-w-xs">
              {agent.description || "Ask me anything about your codebase."}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "rounded-xl px-4 py-3 text-sm",
              msg.role === "user"
                ? "bg-accent/10 border border-accent/20 ml-8"
                : "bg-bg-elevated border border-border-subtle mr-8",
            )}
          >
            <div className="flex items-start gap-2">
              {msg.role === "assistant" && (
                <Bot className="h-4 w-4 text-accent mt-0.5 shrink-0" />
              )}
              {msg.role === "user" && (
                <User className="h-4 w-4 text-accent mt-0.5 shrink-0" />
              )}
              <div className="min-w-0 flex-1">
                <p className="text-text whitespace-pre-wrap">{msg.content}</p>

                {/* Structured Steps */}
                {msg.steps && msg.steps.length > 0 && (
                  <div className="mt-3">
                    <button
                      onClick={() => toggleStep(`msg-${i}`)}
                      className="flex items-center gap-1.5 text-xs text-text-muted hover:text-accent transition-colors mb-2"
                    >
                      {expandedSteps.has(`msg-${i}`) ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                      {msg.steps.length} step{msg.steps.length > 1 ? "s" : ""}
                    </button>

                    <AnimatePresence>
                      {expandedSteps.has(`msg-${i}`) && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2, ease: "easeInOut" }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-1.5 pl-1">
                            {msg.steps.map((step) => {
                              const StepIcon = stepStatusIcons[step.status] || Clock;
                              const stepKey = `msg-${i}-step-${step.id}`;
                              const isExpanded = expandedSteps.has(stepKey);

                              return (
                                <div key={step.id} className="rounded-lg border border-border-subtle bg-bg-surface/50 overflow-hidden">
                                  <button
                                    onClick={() => toggleStep(stepKey)}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-bg-hover/50 transition-colors"
                                  >
                                    <span className="font-mono text-text-muted w-5 text-right shrink-0">
                                      {step.step_number}.
                                    </span>
                                    <StepIcon className={cn("h-3.5 w-3.5 shrink-0", stepStatusColors[step.status])} />
                                    <span className="font-medium text-text truncate flex-1 text-left">
                                      {step.action}
                                    </span>
                                    <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-mono shrink-0", stepStatusBg[step.status])}>
                                      {step.status}
                                    </span>
                                    {isExpanded ? (
                                      <ChevronUp className="h-3 w-3 text-text-muted shrink-0" />
                                    ) : (
                                      <ChevronDown className="h-3 w-3 text-text-muted shrink-0" />
                                    )}
                                  </button>

                                  <AnimatePresence>
                                    {isExpanded && (
                                      <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.15 }}
                                        className="overflow-hidden"
                                      >
                                        <div className="px-3 pb-2.5 pt-0.5 space-y-1.5">
                                          {step.thought && (
                                            <div className="flex items-start gap-2">
                                              <span className="text-[10px] font-mono text-text-muted uppercase shrink-0 mt-0.5">thought</span>
                                              <p className="text-text-muted/70 text-[11px] leading-relaxed">{step.thought}</p>
                                            </div>
                                          )}
                                          {step.observation && (
                                            <div className="flex items-start gap-2">
                                              <span className="text-[10px] font-mono text-text-muted uppercase shrink-0 mt-0.5">output</span>
                                              <p className="text-text-secondary font-mono text-[11px] leading-relaxed">
                                                {step.observation.slice(0, 300)}
                                                {step.observation.length > 300 && "..."}
                                              </p>
                                            </div>
                                          )}
                                          {!step.thought && !step.observation && (
                                            <p className="text-text-muted/50 text-[11px] italic">No additional details</p>
                                          )}
                                        </div>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {msg.timestamp && (
                  <p className="text-[10px] text-text-muted/40 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="bg-bg-elevated border border-border-subtle rounded-xl px-4 py-3 mr-8 animate-pulse">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 px-4 py-3 border-t border-border-subtle bg-bg-elevated/30">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the agent..."
            disabled={loading}
            className="flex-1 rounded-xl bg-bg-surface border border-border-subtle px-4 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className={cn(
              "rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200",
              loading || !input.trim()
                ? "bg-bg-surface text-text-muted border border-border-subtle"
                : "bg-accent text-black hover:bg-accent-hover",
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
