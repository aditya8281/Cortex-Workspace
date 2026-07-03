"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { cn } from "@/shared/lib/utils";
import { DocumentIcon, SearchIcon, BrainIcon, BoltIcon, MenuIcon } from "@/shared/ui/icons";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import { StreamingIndicator } from "./components/StreamingIndicator";
import { ConversationSidebar } from "./components/ConversationSidebar";
import {
  chatApi,
  sendMessage,
  subscribeToStream,
  approveToolCall,
  type Conversation,
  type ChatMessage,
  type Source,
} from "./api";
import { ToolActivity, type ToolEvent } from "./components/ToolActivity";
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
  const skipFetchRef = useRef(false);
  // Track if user has manually scrolled up — suppress auto-scroll during streaming
  const userScrolledUpRef = useRef(false);
  // Track active stream per conversation so we can abort on switch
  const abortRef = useRef<AbortController | null>(null);
  // Track which conversation the current stream belongs to
  const streamConvIdRef = useRef<number | null>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // Per-conversation generation tracking — survives tab switches
  const generatingRef = useRef<Set<number>>(new Set());
  const [generatingIds, setGeneratingIds] = useState<Set<number>>(new Set());
  // Per-conversation message cache — preserves streaming messages across tab switches
  const streamingMessagesRef = useRef<Map<number, ChatMessage[]>>(new Map());
  // Per-conversation thinking cache — accumulates thinking tokens across tab switches
  const thinkingRef = useRef<Map<number, string>>(new Map());
  const [sources, setSources] = useState<Source[]>([]);
  const [installedModels, setInstalledModels] = useState<InstalledModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  // Per-conversation tool events — tracks tool calls/results during streaming
  const toolEventsRef = useRef<Map<number, ToolEvent[]>>(new Map());
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const isCurrentlyStreaming = activeId != null && generatingIds.has(activeId);

  // ── Per-conversation generation tracking ─────────────────────────────
  const setGenerating = useCallback((convId: number, active: boolean) => {
    const next = new Set(generatingRef.current);
    if (active) next.add(convId); else next.delete(convId);
    generatingRef.current = next;
    setGeneratingIds(new Set(next));
    // Persist generating state to sessionStorage so it survives tab switches
    try {
      sessionStorage.setItem("cortex_generating", JSON.stringify([...next]));
    } catch { /* quota exceeded — non-critical */ }
  }, []);

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
    // Restore generating state from sessionStorage (survives tab switches)
    try {
      const raw = sessionStorage.getItem("cortex_generating");
      if (raw) {
        const restored = new Set(JSON.parse(raw) as number[]);
        if (restored.size > 0) {
          generatingRef.current = restored;
          setGeneratingIds(restored);
        }
      }
    } catch { /* non-critical */ }
  }, []);

  const loadConversations = useCallback(async () => {
    try {
      const res = await chatApi.list();
      setConversations(res.conversations);
    } catch { setChatError("Failed to load conversations"); }
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  // Fetch messages when activeId changes
  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    if (skipFetchRef.current) {
      skipFetchRef.current = false;
      return;
    }
    // Always fetch from DB for clean state (user msg + completed responses are there)
    chatApi.get(activeId).then((conv) => {
      setMessages(conv.messages);
      // Check generating state from ref OR sessionStorage (survives tab switches)
      const isGenerating = generatingRef.current.has(activeId) || (() => {
        try {
          const raw = sessionStorage.getItem("cortex_generating");
          return raw ? (JSON.parse(raw) as number[]).includes(activeId) : false;
        } catch { return false; }
      })();
      if (isGenerating) {
        _resubscribeStream(activeId);
      }
    }).catch(() => setMessages([]));
  }, [activeId]);

  useEffect(() => {
    if (userScrolledUpRef.current) return;
    messagesEndRef.current?.scrollIntoView({
      behavior: isCurrentlyStreaming ? "auto" : "smooth",
    });
  }, [messages, isCurrentlyStreaming]);

  // Detect when user scrolls up — suppress auto-scroll
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    userScrolledUpRef.current = !isNearBottom;
  }, []);

  // Attach scroll listener to the messages container
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // Reset user-scrolled-up flag when switching conversations
  useEffect(() => {
    userScrolledUpRef.current = false;
  }, [activeId]);

  const handleDraftChange = useCallback((value: string) => {
    if (activeId) {
      setDrafts((prev) => ({ ...prev, [activeId]: value }));
    }
  }, [activeId]);

  // Abort previous stream WITHOUT touching streaming state
  // (streaming is managed by the caller and the stream lifecycle)
  const abortPrevStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    streamConvIdRef.current = null;
  }, []);

  // ── Resubscribe to an active generation when switching back ──────────
  const _resubscribeStream = async (convId: number) => {
    // If already streaming this conversation, don't resubscribe
    if (streamConvIdRef.current === convId) return;

    abortPrevStream();
    const controller = new AbortController();
    abortRef.current = controller;
    streamConvIdRef.current = convId;

    let assistantContent = "";
    let thinkingContent = "";

    try {
      for await (const event of subscribeToStream(convId, controller.signal)) {
        if (streamConvIdRef.current !== convId) return;
        if (event.type === "thinking" && event.content) {
          thinkingContent += event.content;
          thinkingRef.current.set(convId, thinkingContent);
          // Update visible streaming message with thinking content if viewing this conv
          if (streamConvIdRef.current === convId) {
            setMessages((prev) => {
              if (streamConvIdRef.current !== convId) return prev;
              const existing = prev.filter((m) => m.id !== -1);
              return [...existing, {
                id: -1, role: "assistant" as const, content: assistantContent,
                thinking_content: thinkingContent,
                tokens: event.tokens ?? 0, created_at: new Date().toISOString(),
              }];
            });
          }
        } else if (event.type === "tool_call" && event.tool) {
          const newEvent: ToolEvent = {
            tool: event.tool,
            args: event.args,
            status: "calling",
          };
          const existing = toolEventsRef.current.get(convId) ?? [];
          toolEventsRef.current.set(convId, [...existing, newEvent]);
          if (streamConvIdRef.current === convId) setToolEvents([...toolEventsRef.current.get(convId)!]);
        } else if (event.type === "tool_approval" && event.tool) {
          const events = toolEventsRef.current.get(convId) ?? [];
          const last = events[events.length - 1];
          if (last && last.tool === event.tool && last.status === "calling") {
            last.status = "approval";
            last.callId = event.call_id;
            last.args = event.args ?? last.args;
            last.onApprove = async (callId: string, approved: boolean) => {
              try { await approveToolCall(convId, callId, approved); } catch {}
            };
          }
          toolEventsRef.current.set(convId, [...events]);
          if (streamConvIdRef.current === convId) setToolEvents([...toolEventsRef.current.get(convId)!]);
        } else if (event.type === "tool_result" && event.tool) {
          const events = toolEventsRef.current.get(convId) ?? [];
          const last = events.findLast((e) => e.tool === event.tool && (e.status === "calling" || e.status === "approval"));
          if (last) {
            last.status = event.denied ? "denied" : "done";
            last.result = event.result;
          }
          toolEventsRef.current.set(convId, [...events]);
          if (streamConvIdRef.current === convId) setToolEvents([...toolEventsRef.current.get(convId)!]);
        } else if (event.type === "chunk" && event.content) {
          assistantContent += event.content;
          setMessages((prev) => {
            if (streamConvIdRef.current !== convId) return prev;
            const existing = prev.filter((m) => m.id !== -1);
            return [...existing, {
              id: -1, role: "assistant" as const, content: assistantContent,
              thinking_content: thinkingContent || undefined,
              tokens: event.tokens ?? 0, created_at: new Date().toISOString(),
            }];
          });
        } else if (event.type === "done") {
          setSources(event.sources ?? []);
          setMessages((prev) => {
            if (streamConvIdRef.current !== convId) return prev;
            return prev.map((m) => m.id === -1 ? {
              ...m, id: Date.now(), tokens: event.tokens ?? m.tokens,
              thinking_content: thinkingContent || m.thinking_content,
            } : m);
          });
          thinkingRef.current.delete(convId);
          toolEventsRef.current.delete(convId);
          setToolEvents([]);
          setGenerating(convId, false);
          abortRef.current = null;
          streamConvIdRef.current = null;
          return;
        }
      }
      // Stream ended — generation may have completed while we were away
      thinkingRef.current.delete(convId);
      toolEventsRef.current.delete(convId);
      setToolEvents([]);
      setGenerating(convId, false);
      abortRef.current = null;
      streamConvIdRef.current = null;
    } catch {
      if (streamConvIdRef.current === convId) {
        setGenerating(convId, false);
        abortRef.current = null;
        streamConvIdRef.current = null;
      }
    }
  };

  const handleSend = async (content: string) => {
    let convId = activeId;
    if (!convId) {
      try {
        const conv = await chatApi.create(content.slice(0, 50));
        setConversations((prev) => [conv, ...prev]);
        convId = conv.id;
        const userMsg: ChatMessage = {
          id: Date.now(), role: "user", content, tokens: 0, created_at: new Date().toISOString(),
        };
        setMessages([userMsg]);
        skipFetchRef.current = true;
        setActiveId(conv.id);
        setGenerating(conv.id, true);
        setSources([]);
        setToolEvents([]);
        _streamResponse(convId, content);
        return;
      } catch { return; }
    }

    const userMsg: ChatMessage = {
      id: Date.now(), role: "user", content, tokens: 0, created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setGenerating(convId, true);
    setSources([]);
    _streamResponse(convId, content);
  };

  const _streamResponse = async (convId: number, content: string) => {
    // Abort any previous stream for THIS conversation only
    abortPrevStream();

    const controller = new AbortController();
    abortRef.current = controller;
    streamConvIdRef.current = convId;

    const isStillActive = () => !controller.signal.aborted && streamConvIdRef.current === convId;

    // Helper: update messages for this conversation, whether visible or cached
    const updateMessages = (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
      if (isStillActive()) {
        // Currently viewing this conversation — update visible state
        setMessages((prev) => updater(prev));
      }
      // Always update cache so switching back preserves streaming state
      const current = streamingMessagesRef.current.get(convId) ?? [];
      streamingMessagesRef.current.set(convId, updater(current));
    };

    // Step 1: Tell backend to start generating (returns immediately)
    try {
      await sendMessage(convId, content, selectedModel ?? undefined);
    } catch (err) {
      setGenerating(convId, false);
      updateMessages((prev) => [...prev.filter((m) => m.id !== -1), {
        id: Date.now(), role: "assistant", content: "Failed to start generation. Please try again.",
        tokens: 0, created_at: new Date().toISOString(),
      }]);
      abortRef.current = null;
      streamConvIdRef.current = null;
      return;
    }

    // Step 2: Subscribe to the SSE stream (with auto-reconnect)
    let assistantContent = "";
    let thinkingContent = "";
    const MAX_RECONNECTS = 3;

    for (let attempt = 0; attempt <= MAX_RECONNECTS; attempt++) {
      try {
        for await (const event of subscribeToStream(convId, controller.signal)) {
          if (!isStillActive()) return;
          if (event.type === "thinking" && event.content) {
            thinkingContent += event.content;
            thinkingRef.current.set(convId, thinkingContent);
            updateMessages((prev) => {
              const existing = prev.filter((m) => m.id !== -1);
              return [...existing, {
                id: -1, role: "assistant" as const, content: assistantContent,
                thinking_content: thinkingContent || undefined,
                tokens: event.tokens ?? 0, created_at: new Date().toISOString(),
              }];
            });
          } else if (event.type === "tool_call" && event.tool) {
            const newEvent: ToolEvent = {
              tool: event.tool,
              args: event.args,
              status: "calling",
            };
            const existing = toolEventsRef.current.get(convId) ?? [];
            toolEventsRef.current.set(convId, [...existing, newEvent]);
            if (isStillActive()) setToolEvents([...toolEventsRef.current.get(convId)!]);
          } else if (event.type === "tool_approval" && event.tool) {
            const events = toolEventsRef.current.get(convId) ?? [];
            const last = events[events.length - 1];
            if (last && last.tool === event.tool && last.status === "calling") {
              last.status = "approval";
              last.callId = event.call_id;
              last.args = event.args ?? last.args;
              last.onApprove = async (callId: string, approved: boolean) => {
                try { await approveToolCall(convId, callId, approved); } catch {}
              };
            }
            toolEventsRef.current.set(convId, [...events]);
            if (isStillActive()) setToolEvents([...toolEventsRef.current.get(convId)!]);
          } else if (event.type === "tool_result" && event.tool) {
            const events = toolEventsRef.current.get(convId) ?? [];
            const last = events.findLast((e) => e.tool === event.tool && (e.status === "calling" || e.status === "approval"));
            if (last) {
              last.status = event.denied ? "denied" : "done";
              last.result = event.result;
            }
            toolEventsRef.current.set(convId, [...events]);
            if (isStillActive()) setToolEvents([...toolEventsRef.current.get(convId)!]);
          } else if (event.type === "chunk" && event.content) {
            assistantContent += event.content;
            updateMessages((prev) => {
              const existing = prev.filter((m) => m.id !== -1);
              return [...existing, {
                id: -1, role: "assistant" as const, content: assistantContent,
                thinking_content: thinkingContent || undefined,
                tokens: event.tokens ?? 0, created_at: new Date().toISOString(),
              }];
            });
          } else if (event.type === "done") {
            if (isStillActive()) setSources(event.sources ?? []);
            updateMessages((prev) =>
              prev.map((m) => m.id === -1 ? {
                ...m, id: Date.now(), tokens: event.tokens ?? m.tokens,
                thinking_content: thinkingContent || m.thinking_content,
              } : m)
            );
            // Successfully completed — clear cache for this conv (response is now in DB)
            streamingMessagesRef.current.delete(convId);
            thinkingRef.current.delete(convId);
            toolEventsRef.current.delete(convId);
            setToolEvents([]);
            setGenerating(convId, false);
            abortRef.current = null;
            streamConvIdRef.current = null;
            // Refresh conversation list — backend may have generated a new title
            loadConversations();
            return;
          }
        }
        // Stream ended without "done" — reconnect if still active
        if (!isStillActive()) return;
        if (attempt < MAX_RECONNECTS) {
          await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
          continue;
        }
      } catch (err) {
        if (!isStillActive()) return;
        if (attempt < MAX_RECONNECTS) {
          await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
          continue;
        }
        updateMessages((prev) => [...prev.filter((m) => m.id !== -1), {
          id: Date.now(), role: "assistant", content: "Connection lost. The response may still be generating — try refreshing.",
          tokens: 0, created_at: new Date().toISOString(),
        }]);
      }
    }

    streamingMessagesRef.current.delete(convId);
    thinkingRef.current.delete(convId);
    toolEventsRef.current.delete(convId);
    setToolEvents([]);
    setGenerating(convId, false);
    abortRef.current = null;
    streamConvIdRef.current = null;
  };

  // Handle visibility changes (tab switch): pause SSE when hidden,
  // reconnect when visible if generation is still active.
  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.hidden) {
        // Hide: abort SSE — backend keeps generating as a detached task
        abortRef.current?.abort();
        abortRef.current = null;
      } else {
        // Show: reconnect if this conversation was generating
        if (activeId) {
          const isGenerating = generatingRef.current.has(activeId) || (() => {
            try {
              const raw = sessionStorage.getItem("cortex_generating");
              return raw ? (JSON.parse(raw) as number[]).includes(activeId) : false;
            } catch { return false; }
          })();
          if (isGenerating && streamConvIdRef.current !== activeId) {
            _resubscribeStream(activeId);
          }
        }
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [activeId]);

  if (loading) return null;
  if (!user) return null;

  const activeConv = conversations.find((c) => c.id === activeId);

  const handleSelectConversation = (id: number) => {
    abortPrevStream();
    setSources([]);
    setToolEvents(toolEventsRef.current.get(id) ?? []);
    setActiveId(id);
    setSidebarOpen(false);
    // Don't clear streaming — generatingRef tracks per-conversation state
  };

  return (
    <div className="relative flex h-full min-h-0 flex-col bg-bg-base">
      <ConversationSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        activeId={activeId}
        generatingIds={generatingIds}
        onSelect={handleSelectConversation}
        onDelete={(id) => {
          if (activeId === id) {
            abortPrevStream();
            setGenerating(id, false);
          }
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
            abortPrevStream();
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
      <div className="flex flex-1 flex-col min-h-0 min-w-0">
        {/* ── Header ──────────────────────────────────────────────── */}
        <div
          className={cn(
            "flex h-12 items-center gap-3 px-4 flex-shrink-0",
            "border-b border-border-subtle",
            "motion-safe:transition-shadow motion-safe:duration-500",
            // Subtle cyan glow along bottom edge when a conversation is active
            activeConv && "shadow-[inset_0_-1px_0_rgba(0,172,193,0.12)]",
          )}
        >
          <button
            onClick={() => setSidebarOpen((prev) => !prev)}
            className={cn(
              "flex items-center justify-center h-8 w-8 rounded-lg",
              "text-text-muted hover:text-text-primary hover:bg-bg-surface",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
            aria-label="Open conversations"
          >
            <MenuIcon />
          </button>

          {/* Separator — thin vertical rule, not a dot */}
          <span className="h-4 w-px bg-border-subtle" />

          {activeConv ? (
            <span className="text-sm font-medium text-text-primary truncate max-w-[280px]">
              {activeConv.title}
            </span>
          ) : (
            <span className="text-xs font-medium text-text-muted tracking-wide uppercase">
              New chat
            </span>
          )}

          <div className="flex-1" />

          {/* Model selector — styled as a proper chip */}
          <div className="relative">
            <select
              value={selectedModel ?? ""}
              onChange={(e) => {
                const val = e.target.value || null;
                setSelectedModel(val);
                if (val) setDefaultModel(val);
              }}
              aria-label="Select model"
              className={cn(
                "appearance-none rounded-lg border border-border-subtle bg-bg-elevated",
                "h-7 pl-2.5 pr-7 text-[11px] text-text-secondary font-mono",
                "outline-none cursor-pointer",
                "hover:border-border-default hover:text-text-primary",
                "focus:border-accent-red/40",
                "motion-safe:transition-colors motion-safe:duration-150",
              )}
            >
              <option value="">Default model</option>
              {installedModels.map((m) => (
                <option key={m.model_id} value={m.model_id}>{m.display_name}</option>
              ))}
            </select>
            {/* Custom chevron — native select arrows are ugly */}
            <svg
              className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-text-muted"
              width="10" height="10" viewBox="0 0 16 16" fill="none"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
            >
              <path d="M4 6l4 4 4-4" />
            </svg>
          </div>
        </div>

        {/* ── Messages ────────────────────────────────────────────── */}
        <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 py-4">
          {!activeId ? (
            /* ── Empty state ── */
            <div className="relative flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto">

              {/* Neural icon — the brain/synapse mark */}
              <div className="chat-empty-entrance relative mb-8">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-accent-cyan/15 bg-accent-cyan-muted/10">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    {/* Synapse/neuron icon — organic, not geometric */}
                    <circle cx="12" cy="12" r="3" strokeOpacity="0.6" />
                    <circle cx="12" cy="12" r="8" strokeOpacity="0.2" />
                    <path d="M12 4v2M12 18v2M4 12h2M18 12h2" strokeOpacity="0.35" />
                    <path d="M7.05 7.05l1.41 1.41M15.54 15.54l1.41 1.41M7.05 16.95l1.41-1.41M15.54 8.46l1.41-1.41" strokeOpacity="0.25" />
                  </svg>
                </div>
                {/* Subtle pulse ring — perpetual micro-animation (§4 design taste) */}
                <span className="pointer-events-none absolute inset-0 rounded-2xl border border-accent-cyan/10 motion-safe:animate-pulse" />
              </div>

              <h2 className="chat-empty-entrance chat-empty-delay-1 text-display font-semibold text-text-primary tracking-tight">
                Ask Cortex anything
              </h2>
              <p className="chat-empty-entrance chat-empty-delay-2 mt-3 text-sm text-text-secondary max-w-[42ch] leading-relaxed">
                Questions about your code, research, analysis, or a conversation.
                Cortex has context.
              </p>

              <div className="chat-empty-entrance chat-empty-delay-3 mt-8 grid grid-cols-2 gap-2.5 w-full">
                {suggestedPrompts.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => handleSend(p.prompt)}
                    aria-label={`Suggested prompt: ${p.label}`}
                    className={cn(
                      "group relative rounded-xl border border-border-subtle p-3.5 text-left",
                      "bg-bg-elevated/60",
                      "hover:border-accent-cyan/20 hover:bg-bg-surface/80",
                      "active:scale-[0.98]",
                      "motion-safe:transition-all motion-safe:duration-200",
                    )}
                  >
                    {/* Subtle left accent bar on hover */}
                    <span className="pointer-events-none absolute left-0 top-3 bottom-3 w-[2px] rounded-full bg-accent-cyan/0 group-hover:bg-accent-cyan/40 motion-safe:transition-colors motion-safe:duration-200" />
                    <span className="flex items-center justify-center h-7 w-7 rounded-lg bg-bg-surface text-text-muted group-hover:text-accent-cyan motion-safe:transition-colors motion-safe:duration-150 mb-2">
                      {p.icon}
                    </span>
                    <span className="block text-[13px] text-text-primary font-medium leading-snug">{p.label}</span>
                    <span className="block text-[11px] text-text-muted mt-1 leading-snug">{p.description}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4 pb-4">
              {messages.map((msg, i) => (
                <MessageBubble
                  key={msg.id || i}
                  role={msg.role === "system" ? "assistant" : msg.role}
                  content={msg.content}
                  thinkingContent={msg.thinking_content ?? undefined}
                  isStreaming={msg.id === -1}
                  timestamp={msg.created_at}
                  style={{ "--i": i } as React.CSSProperties}
                />
              ))}
              {/* Tool activity — shown during streaming */}
              {activeId && toolEvents.length > 0 && (
                <div className="flex flex-col gap-1.5 pl-1">
                  {toolEvents.map((evt, i) => (
                    <ToolActivity key={`${evt.tool}-${i}`} {...evt} />
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Sources */}
        {sources.length > 0 && (
          <div className="border-t border-border-subtle px-4 sm:px-6 py-2">
            <details className="group" aria-label={`Sources panel with ${sources.length} items`}>
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

        {/* Context ribbon */}
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

        {/* Streaming indicator — centered bar above input */}
        {activeId && isCurrentlyStreaming && (
          <div className="flex justify-center px-4 sm:px-6 pb-3">
            <StreamingIndicator centered />
          </div>
        )}

        {/* Input */}
        <div className="pb-20">
          <ChatInput
            onSend={handleSend}
            onTyping={sendTyping}
            disabled={isCurrentlyStreaming}
            initialValue={drafts[activeId ?? 0] ?? ""}
            onValueChange={handleDraftChange}
          />
        </div>
      </div>
    </div>
  );
}

const suggestedPrompts = [
  { icon: <DocumentIcon size={16} />, label: "Summarize", description: "Key concepts and architecture of this project", prompt: "Can you help me summarize the key concepts of this project?" },
  { icon: <SearchIcon size={16} />, label: "Search code", description: "Find authentication, WebSocket, and session patterns", prompt: "Search the codebase for anything related to authentication and WebSocket connections" },
  { icon: <BrainIcon size={16} />, label: "System state", description: "Memory, knowledge graph, and health stats", prompt: "Show me the current memory and knowledge graph statistics" },
  { icon: <BoltIcon size={16} />, label: "Quick answer", description: "Architecture overview and system design", prompt: "What is the architecture of this system?" },
];
