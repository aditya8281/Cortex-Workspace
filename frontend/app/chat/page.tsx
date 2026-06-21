"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, MessageSquare, Trash2, Send, Brain, Cpu } from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import Card from "@/shared/ui/Card";
import Dropdown, { DropdownItem } from "@/shared/ui/Dropdown";
import { useAuth } from "@/shared/auth/AuthProvider";
import { api, getCsrfToken } from "@/shared/api/client";
import { toast } from "sonner";
import type { Conversation } from "@/shared/types";
import { MarkdownRenderer } from "@/shared/components/MarkdownRenderer";

interface Message {
  role: string;
  content: string;
  tokens?: number;
  created_at: string;
  sources?: Array<{ file_path: string; score: number; content: string }>;
}

function SourceReferences({ sources }: { sources: Array<{ file_path: string; score: number; content: string }> }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {sources.map((s, i) => (
        <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-accent/10 text-accent border border-accent/20">
          [{i + 1}] {s.file_path.split("/").pop()}
        </span>
      ))}
    </div>
  );
}

export default function ChatPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const messagesEnd = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    api.get<{ conversations: Conversation[] }>("/api/v1/conversations").then((data) => {
      setConversations(data.conversations);
      if (data.conversations.length > 0 && !activeId) {
        setActiveId(data.conversations[0].id);
      }
    }).catch((err) => {
      console.error("Failed to load conversations:", err);
      toast.error("Failed to load conversations");
    });
  }, [user]);

  useEffect(() => {
    if (!activeId) return;
    api.get<{ messages: Message[] }>(`/api/v1/conversations/${activeId}`).then((data) => {
      setMessages(data.messages);
    }).catch((err) => {
      console.error("Failed to load messages:", err);
      toast.error("Failed to load messages");
    });
  }, [activeId]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  useEffect(() => {
    api.get<{ models: Array<{ name: string }> }>("/api/v1/models").then((data) => {
      setAvailableModels(data.models.map((m) => m.name));
    }).catch(() => {});
  }, []);

  const createConversation = async () => {
    const data = await api.post<{ id: number }>("/api/v1/conversations", {
      title: "New Conversation",
    });
    setConversations((prev) => [
      {
        id: data.id,
        title: "New Conversation",
        repo_id: null,
        model_used: null,
        message_count: 0,
        total_tokens: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      ...prev,
    ]);
    setActiveId(data.id);
    setMessages([]);
  };

  const sendMessage = useCallback(async () => {
    if (!input.trim() || !activeId || sending) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);
    setStreamingContent("");

    try {
      const csrfToken = getCsrfToken();
      const res = await fetch(`/api/v1/conversations/${activeId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "x-csrf-token": csrfToken } : {}),
        },
        body: JSON.stringify({ content: userMsg.content, model: selectedModel || undefined }),
        credentials: "include",
        signal: abortRef.current?.signal,
      });

      if (!res.ok) throw new Error("Failed to send message");

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "chunk") {
              setStreamingContent((prev) => prev + event.content);
            } else if (event.type === "done") {
              const finalSources = event.sources || [];
              setStreamingContent((prevContent) => {
                const content = prevContent || event.content || "";
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content,
                    tokens: event.total_tokens,
                    created_at: new Date().toISOString(),
                    sources: finalSources,
                  },
                ]);
                return "";
              });
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") return;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Failed to get response. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
      setStreamingContent("");
    }
  }, [input, activeId, sending, selectedModel]);

  const deleteConversation = async (id: number) => {
    await api.delete(`/api/v1/conversations/${id}`);
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) {
      const next = conversations.find((c) => c.id !== id);
      setActiveId(next?.id ?? null);
      if (!next) setMessages([]);
    }
  };

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <div className="relative z-10 flex h-[calc(100vh-4rem)]">
        {/* Sidebar */}
        <div className="w-64 border-r border-border-subtle p-4 flex flex-col">
          <button
            onClick={createConversation}
            className="w-full py-2 rounded-lg bg-accent/10 text-accent text-sm font-medium hover:bg-accent/20 transition-colors flex items-center justify-center gap-2 mb-4"
          >
            <Plus size={14} /> New Chat
          </button>
          <div className="flex-1 overflow-y-auto space-y-1">
            {conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => setActiveId(c.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors group ${
                  activeId === c.id
                    ? "bg-bg-hover text-text"
                    : "text-text-secondary hover:bg-bg-hover/50"
                }`}
              >
                <MessageSquare size={14} />
                <span className="flex-1 truncate text-sm">{c.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(c.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-danger"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && !streamingContent && (
              <div className="flex items-center justify-center h-full">
                <p className="text-text-muted text-sm">
                  Start a conversation with Cortex.
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <Card
                  className={`max-w-2xl px-4 py-3 text-sm ${
                    msg.role === "user" ? "bg-accent/10 border-accent/20" : ""
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <MarkdownRenderer content={msg.content} />
                  ) : (
                    <p className="text-text whitespace-pre-wrap">{msg.content}</p>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <SourceReferences sources={msg.sources} />
                  )}
                  {msg.tokens && (
                    <p className="text-[10px] text-text-muted mt-1">
                      {msg.tokens} tokens
                    </p>
                  )}
                </Card>
              </motion.div>
            ))}
            {sending && streamingContent && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <Card className="max-w-2xl px-4 py-3 text-sm">
                  <MarkdownRenderer content={streamingContent} />
                  <div className="flex items-center gap-1 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                  </div>
                </Card>
              </motion.div>
            )}
            {sending && !streamingContent && (
              <div className="flex justify-start">
                <Card className="px-4 py-3 text-sm">
                  <div className="flex items-center gap-2 text-text-muted">
                    <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                    Thinking...
                  </div>
                </Card>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-border-subtle">
{availableModels.length > 0 && (
              <div className="flex gap-2 max-w-3xl mx-auto mb-2">
                <Dropdown
                  trigger={
                    <button
                      type="button"
                      className="flex items-center gap-2 text-xs bg-bg-surface border border-border-subtle rounded-lg px-3 py-1.5 text-text-secondary hover:border-accent/50 transition-colors"
                    >
                      {selectedModel ? <Cpu size={12} /> : <Brain size={12} />}
                      <span>{selectedModel || "Default model"}</span>
                    </button>
                  }
                >
                  <DropdownItem
                    onClick={() => setSelectedModel("")}
                    className={!selectedModel ? "bg-accent/10 text-accent" : ""}
                  >
                    <Brain size={14} />
                    Default model
                  </DropdownItem>
                  {availableModels.map((m) => (
                    <DropdownItem
                      key={m}
                      onClick={() => setSelectedModel(m)}
                      className={selectedModel === m ? "bg-accent/10 text-accent" : ""}
                    >
                      <Cpu size={14} />
                      {m}
                    </DropdownItem>
                  ))}
                </Dropdown>
              </div>
            )}
            <div className="flex gap-2 max-w-3xl mx-auto">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask Cortex anything..."
                className="flex-1 bg-bg-surface border border-border-subtle rounded-lg px-4 py-3 text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
                disabled={sending}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || sending}
                className="px-4 py-3 rounded-lg bg-accent text-bg font-medium hover:bg-accent-bright transition-colors disabled:opacity-50"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
