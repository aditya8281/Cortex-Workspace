"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Modal } from "@/shared/ui/Modal";
import { ConversationList } from "./components/ConversationList";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import { StreamingIndicator } from "./components/StreamingIndicator";
import {
  chatApi,
  streamChat,
  type Conversation,
  type ChatMessage,
  type Source,
} from "./api";

export default function ChatPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);

  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadConversations = useCallback(async () => {
    try {
      const res = await chatApi.list();
      setConversations(res.conversations);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (!activeId) return;
    chatApi
      .get(activeId)
      .then((conv) => setMessages(conv.messages))
      .catch(() => setMessages([]));
  }, [activeId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try {
      const conv = await chatApi.create(newTitle.trim());
      setConversations((prev) => [conv, ...prev]);
      setActiveId(conv.id);
      setMessages([]);
      setShowNew(false);
      setNewTitle("");
    } catch {
      // ignore
    }
  };

  const handleSend = async (content: string) => {
    let convId = activeId;

    // Auto-create conversation if none active
    if (!convId) {
      try {
        const conv = await chatApi.create(content.slice(0, 50));
        setConversations((prev) => [conv, ...prev]);
        convId = conv.id;
        setActiveId(conv.id);
        setMessages([]);
      } catch {
        return;
      }
    }

    // Add user message optimistically
    const userMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      content,
      tokens: 0,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setStreaming(true);
    setSources([]);

    let assistantContent = "";

    try {
      for await (const event of streamChat(convId, content)) {
        if (event.type === "chunk" && event.content) {
          assistantContent += event.content;
          setMessages((prev) => {
            const existing = prev.filter((m) => m.id !== -1);
            return [
              ...existing,
              {
                id: -1,
                role: "assistant" as const,
                content: assistantContent,
                tokens: event.tokens ?? 0,
                created_at: new Date().toISOString(),
              },
            ];
          });
        } else if (event.type === "done") {
          setSources(event.sources ?? []);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === -1
                ? { ...m, id: Date.now(), tokens: event.tokens ?? m.tokens }
                : m,
            ),
          );
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== -1),
        {
          id: Date.now(),
          role: "assistant",
          content: "Connection error. Please try again.",
          tokens: 0,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setStreaming(false);
    }
  };

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="flex h-full gap-0 -m-6">
        {/* Conversation sidebar */}
        <div className="hidden sm:flex w-64 flex-shrink-0 flex-col border-r border-border-subtle bg-bg-elevated">
          <div className="p-3 border-b border-border-subtle">
            <Button
              variant="primary"
              size="sm"
              className="w-full"
              onClick={() => setShowNew(true)}
            >
              New Chat
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ConversationList
              conversations={conversations}
              activeId={activeId}
              onSelect={(id) => {
                setActiveId(id);
                setSources([]);
              }}
            />
          </div>
        </div>

        {/* Chat area */}
        <div className="flex flex-1 flex-col min-w-0">
          {!activeId ? (
            <div className="flex-1 flex items-center justify-center p-6">
              <EmptyState
                title="Start a conversation"
                description="Ask CORTEX anything about your codebase or knowledge"
                action={
                  <Button onClick={() => setShowNew(true)}>New Chat</Button>
                }
              />
            </div>
          ) : (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                {messages.map((msg, i) => (
                  <MessageBubble key={msg.id || i} message={msg} />
                ))}
                {streaming && <StreamingIndicator />}
                <div ref={messagesEndRef} />
              </div>

              {/* Sources */}
              {sources.length > 0 && (
                <div className="border-t border-border-subtle px-6 py-3">
                  <p className="text-xs text-text-muted mb-2 font-medium">Sources</p>
                  <div className="flex flex-wrap gap-2">
                    {sources.map((src, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center rounded-md bg-bg-surface px-2 py-1 text-xs text-text-secondary font-mono"
                      >
                        {src.file_path}
                        <span className="ml-1 text-text-muted">
                          ({Math.round(src.score * 100)}%)
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Input */}
              <ChatInput
                onSend={handleSend}
                disabled={streaming}
              />
            </>
          )}
        </div>
      </div>

      {/* New conversation modal */}
      <Modal open={showNew} onClose={() => setShowNew(false)} title="New Chat">
        <div className="space-y-4">
          <Input
            label="Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="What do you want to talk about?"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
            }}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowNew(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={!newTitle.trim()}>
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </AppShell>
  );
}
