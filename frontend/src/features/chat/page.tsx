"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { cn } from "@/shared/lib/utils";
import { DocumentIcon, SearchIcon, BrainIcon, LightningIcon } from "@/shared/ui/icons";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import { StreamingIndicator } from "./components/StreamingIndicator";
import { ConversationSidebar } from "./components/ConversationSidebar";
import {
  chatApi,
  streamChat,
  type Conversation,
  type ChatMessage,
  type Source,
} from "./api";
import {
  downloads as modelsDownloads,
  getDefaultModel,
  setDefaultModel,
  type InstalledModel,
} from "@/features/models/api";
import { useChatTyping } from "@/shared/ws/useChatTyping";

export default function ChatPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [installedModels, setInstalledModels] = useState<InstalledModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Typing indicators
  const { sendTyping, isOthersTyping, typingCount } = useChatTyping({
    conversationId: activeId,
    userId: user ? Number(user.id) : undefined,
  });

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    setSelectedModel(getDefaultModel());
    modelsDownloads.installed().then((res) => setInstalledModels(res.models)).catch(() => {});
  }, []);

  const loadConversations = useCallback(async () => {
    try {
      const res = await chatApi.list();
      setConversations(res.conversations);
    } catch { setChatError("Failed to load conversations"); }
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  useEffect(() => {
    if (!activeId) return;
    chatApi.get(activeId).then((conv) => setMessages(conv.messages)).catch(() => setMessages([]));
  }, [activeId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const handleSend = async (content: string) => {
    let convId = activeId;
    if (!convId) {
      try {
        const conv = await chatApi.create(content.slice(0, 50));
        setConversations((prev) => [conv, ...prev]);
        convId = conv.id;
        setActiveId(conv.id);
        setMessages([]);
      } catch { return; }
    }

    const userMsg: ChatMessage = {
      id: Date.now(), role: "user", content, tokens: 0, created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setStreaming(true);
    setSources([]);

    let assistantContent = "";
    try {
      for await (const event of streamChat(convId, content, selectedModel ?? undefined)) {
        if (event.type === "chunk" && event.content) {
          assistantContent += event.content;
          setMessages((prev) => {
            const existing = prev.filter((m) => m.id !== -1);
            return [...existing, {
              id: -1, role: "assistant" as const, content: assistantContent,
              tokens: event.tokens ?? 0, created_at: new Date().toISOString(),
            }];
          });
        } else if (event.type === "done") {
          setSources(event.sources ?? []);
          setMessages((prev) => prev.map((m) => m.id === -1 ? { ...m, id: Date.now(), tokens: event.tokens ?? m.tokens } : m));
        }
      }
    } catch {
      setMessages((prev) => [...prev.filter((m) => m.id !== -1), {
        id: Date.now(), role: "assistant", content: "Connection error. Please try again.",
        tokens: 0, created_at: new Date().toISOString(),
      }]);
    } finally { setStreaming(false); }
  };

  if (loading || !user) return null;

  const activeConv = conversations.find((c) => c.id === activeId);

  return (
    <div className="relative flex h-full flex-col bg-bg-base">
      {/* Slide-over conversation sidebar */}
      <ConversationSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => { setActiveId(id); setSources([]); setSidebarOpen(false); }}
        onDelete={(id) => {
          setConversations((prev) => prev.filter((c) => c.id !== id));
          if (activeId === id) { setActiveId(null); setMessages([]); }
          chatApi.delete(id).catch(() => setChatError("Failed to delete"));
        }}
        onRename={(id, title) => {
          setConversations((prev) => prev.map((c) => c.id === id ? { ...c, title } : c));
          chatApi.rename(id, title).catch(() => setChatError("Failed to rename"));
        }}
        onNewChat={async () => {
          try {
            const conv = await chatApi.create("New conversation");
            setConversations((prev) => [conv, ...prev]);
            setActiveId(conv.id);
            setMessages([]);
            setSidebarOpen(false);
          } catch { setChatError("Failed to create"); }
        }}
        error={chatError}
        onClearError={() => setChatError(null)}
      />

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Top bar — menu + model */}
        <div className="flex h-11 items-center gap-2 border-b border-border-subtle px-4 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="flex items-center justify-center h-8 w-8 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
            aria-label="Open conversations"
          >
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M2 3h12M2 8h12M2 13h8" />
            </svg>
          </button>
          <span className="text-border-default text-sm">·</span>
          {activeConv && (
            <>
              <span className="text-sm font-medium text-text-primary truncate">{activeConv.title}</span>
              <span className="text-border-default text-sm">·</span>
            </>
          )}
          <div className="flex-1" />
          <select
            value={selectedModel ?? ""}
            onChange={(e) => {
              const val = e.target.value || null;
              setSelectedModel(val);
              if (val) setDefaultModel(val);
            }}
            className="rounded-md border border-border-subtle bg-bg-surface px-2 py-1 text-xs text-text-secondary font-mono outline-none focus:border-accent-red/50 motion-safe:transition-colors motion-safe:duration-150"
          >
            <option value="">Default model</option>
            {installedModels.map((m) => (
              <option key={m.model_id} value={m.model_id}>{m.display_name}</option>
            ))}
          </select>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-6 py-4">
          {!activeId ? (
            /* Empty state — welcome message */
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-cyan-muted text-accent-cyan">
                <svg width="28" height="28" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 0L16 8L8 16L0 8L8 0Z" />
                </svg>
              </div>
              <h2 className="text-headline font-semibold text-text-primary">Ask Cortex anything</h2>
              <p className="mt-2 text-sm text-text-secondary">
                Questions, code analysis, research, or just a conversation.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-2 w-full">
                {suggestedPrompts.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => handleSend(p.prompt)}
                    className={cn(
                      "rounded-xl border border-border-subtle p-3 text-left text-xs",
                      "bg-bg-widget backdrop-blur-xl",
                      "hover:border-border-default hover:-translate-y-0.5",
                      "motion-safe:transition-all motion-safe:duration-200",
                    )}
                  >
                    <span className="text-base block mb-1">{p.icon}</span>
                    <span className="text-text-primary font-medium">{p.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((msg, i) => (
                <MessageBubble
                  key={msg.id || i}
                  role={msg.role === "system" ? "assistant" : msg.role}
                  content={msg.content}
                  timestamp={msg.created_at}
                />
              ))}
              {streaming && <StreamingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Sources */}
        {sources.length > 0 && (
          <div className="border-t border-border-subtle px-4 sm:px-6 py-2">
            <details className="group">
              <summary className="text-xs text-text-muted font-medium cursor-pointer hover:text-text-secondary motion-safe:transition-colors motion-safe:duration-150">
                Sources ({sources.length})
              </summary>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {sources.map((s, i) => (
                  <span key={i} className="rounded-md border border-border-subtle bg-bg-elevated px-2 py-0.5 text-xs text-text-muted font-mono">
                    {s.file_path.split("/").pop()}
                  </span>
                ))}
              </div>
            </details>
          </div>
        )}

        {/* Typing indicator */}
        {isOthersTyping && (
          <div className="px-4 sm:px-6 py-1">
            <p className="text-xs text-text-muted italic">
              Someone is typing{typingCount > 1 ? ` (${typingCount})` : ""}…
            </p>
          </div>
        )}

        {/* Context ribbon (below input) */}
        <div id="context-ribbon" className="px-4 sm:px-6 pb-1">
          {(activeId && messages.length > 0) ? (
            <div className="flex items-center gap-2 text-[10px] text-text-muted">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent-cyan" />
              <span>{messages.length} message{messages.length !== 1 ? "s" : ""}</span>
              {selectedModel && (
                <>
                  <span className="w-px h-3 bg-border-subtle" />
                  <span className="font-mono">{selectedModel}</span>
                </>
              )}
            </div>
          ) : null}
        </div>

        {/* Input */}
        <ChatInput
          onSend={handleSend}
          onTyping={sendTyping}
          disabled={streaming}
        />
      </div>
    </div>
  );
}

const suggestedPrompts = [
  { icon: <DocumentIcon size={16} />, label: "Summarize this", prompt: "Can you help me summarize the key concepts of this project?" },
  { icon: <SearchIcon size={16} />, label: "Find in codebase", prompt: "Search the codebase for anything related to authentication and WebSocket connections" },
  { icon: <BrainIcon size={16} />, label: "Memory stats", prompt: "Show me the current memory and knowledge graph statistics" },
  { icon: <LightningIcon size={16} />, label: "Quick answer", prompt: "What is the architecture of this system?" },
];
