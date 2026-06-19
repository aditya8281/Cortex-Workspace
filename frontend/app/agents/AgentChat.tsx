"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, ChevronDown, ChevronUp } from "lucide-react";
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

export default function AgentChat({ agent, onRunComplete }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function toggleSteps(index: number) {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
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
      const run = result.run;

      // Fetch steps for detail
      let steps: AgentStep[] = [];
      try {
        const detail = await agentApi.getRun(run.id);
        steps = detail.steps;
      } catch {
        // Steps fetch failed, continue without them
      }

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

                {/* Steps toggle */}
                {msg.steps && msg.steps.length > 0 && (
                  <div className="mt-2">
                    <button
                      onClick={() => toggleSteps(i)}
                      className="flex items-center gap-1 text-xs text-text-muted hover:text-accent transition-colors"
                    >
                      {expandedSteps.has(i) ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                      {msg.steps.length} step{msg.steps.length > 1 ? "s" : ""}
                    </button>

                    {expandedSteps.has(i) && (
                      <div className="mt-2 space-y-2 pl-2 border-l border-border-subtle">
                        {msg.steps.map((step) => (
                          <div key={step.id} className="text-xs">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-accent">#{step.step_number}</span>
                              <span className="text-text-muted">{step.action}</span>
                              <span
                                className={cn(
                                  "px-1.5 py-0.5 rounded text-[10px] font-mono",
                                  step.status === "completed"
                                    ? "bg-success/10 text-success"
                                    : step.status === "failed"
                                      ? "bg-error/10 text-error"
                                      : "bg-bg-surface text-text-muted",
                                )}
                              >
                                {step.status}
                              </span>
                            </div>
                            {step.thought && (
                              <p className="text-text-muted/60 mt-0.5">{step.thought}</p>
                            )}
                            {step.observation && (
                              <p className="text-text-secondary mt-0.5 font-mono text-[11px]">
                                {step.observation.slice(0, 200)}
                                {step.observation.length > 200 && "..."}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
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
