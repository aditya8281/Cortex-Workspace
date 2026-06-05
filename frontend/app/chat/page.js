"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Badge, Button, Card, Input, Loader } from "../../src/shared/ui";

function createSessionId() {
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

function formatLatency(ms) {
  return `${Math.max(0, Math.round(ms))} ms`;
}

function MessageCard({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={["flex w-full", isUser ? "justify-end" : "justify-start"].join(" ")}>
      <div
        className={[
          "max-w-[min(760px,92%)] rounded-cortex-lg border p-cortex-16 backdrop-blur-xl",
          isUser
            ? "border-cortex-cyan/20 bg-cortex-surface shadow-cortex-cyan"
            : "border-cortex-border bg-cortex-surface",
        ].join(" ")}
      >
        <div className="mb-cortex-8 flex items-center justify-between gap-cortex-12">
          <div className="flex items-center gap-cortex-8">
            <Badge variant={isUser ? "cyan" : "neutral"}>{isUser ? "user" : "cortex"}</Badge>
            {message.model ? (
              <Badge variant="neutral">model: {message.model}</Badge>
            ) : null}
          </div>
          {typeof message.latencyMs === "number" ? (
            <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
              {formatLatency(message.latencyMs)}
            </span>
          ) : null}
        </div>

        <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-cortex-text">
          {message.content}
        </pre>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [sessions, setSessions] = useState(() => [
    {
      id: createSessionId(),
      title: "Session 01",
      messages: [
        {
          role: "assistant",
          content: "Cortex ready. Enter a command.",
          model: "auto",
        },
      ],
    },
  ]);
  const [activeSessionId, setActiveSessionId] = useState(() => sessions[0].id);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [model] = useState("auto");
  const endRef = useRef(null);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) || sessions[0],
    [sessions, activeSessionId]
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeSession?.messages?.length, loading]);

  function updateActiveSession(updater) {
    setSessions((current) =>
      current.map((session) => {
        if (session.id !== activeSessionId) return session;
        return updater(session);
      })
    );
  }

  function startNewSession() {
    const id = createSessionId();
    setSessions((current) => [
      {
        id,
        title: `Session ${String(current.length + 1).padStart(2, "0")}`,
        messages: [],
      },
      ...current,
    ]);
    setActiveSessionId(id);
    setError("");
    setInput("");
  }

  async function submitMessage() {
    const message = input.trim();
    if (!message || loading) return;

    const userMessage = {
      role: "user",
      content: message,
      model,
    };

    const nextMessages = [...(activeSession?.messages || []), userMessage];
    updateActiveSession((session) => ({
      ...session,
      messages: nextMessages,
    }));

    setInput("");
    setLoading(true);
    setError("");

    const startedAt = performance.now();
    updateActiveSession((session) => ({
      ...session,
      messages: [
        ...nextMessages,
        {
          role: "assistant",
          content: "Cortex processing...",
          model,
          pending: true,
        },
      ],
    }));

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          sessionId: activeSession.id,
          model,
        }),
      });

      const data = await response.json();
      const latencyMs = performance.now() - startedAt;

      if (!response.ok) {
        throw new Error(data?.error || "Chat request failed");
      }

      updateActiveSession((session) => {
        const baseMessages = session.messages.filter((item) => !item.pending);
        return {
          ...session,
          messages: [
            ...baseMessages,
            {
              role: "assistant",
              content: data.response || "No response returned.",
              model: data.routing_info?.model || model,
              latencyMs,
              executionId: data.execution_id || null,
            },
          ],
          sessionId: data.session_id || session.id,
        };
      });

      if (data.session_id && data.session_id !== activeSession.id) {
        setSessions((current) =>
          current.map((session) =>
            session.id === activeSession.id ? { ...session, id: data.session_id } : session
          )
        );
        setActiveSessionId(data.session_id);
      }
    } catch (nextError) {
      const latencyMs = performance.now() - startedAt;
      const messageText = nextError instanceof Error ? nextError.message : "Chat request failed";

      setError(messageText);
      updateActiveSession((session) => {
        const baseMessages = session.messages.filter((item) => !item.pending);
        return {
          ...session,
          messages: [
            ...baseMessages,
            {
              role: "assistant",
              content: `Error: ${messageText}`,
              model,
              latencyMs,
              error: true,
            },
          ],
        };
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid gap-cortex-16 xl:grid-cols-[280px_minmax(0,1fr)]">
      <Card className="order-2 xl:order-1">
        <div className="mb-cortex-16 flex items-center justify-between gap-cortex-12">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Chat</p>
            <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Terminal Response Channel</h1>
          </div>
          <Badge variant="cyan">model: {model}</Badge>
        </div>

        <div className="flex h-[62vh] flex-col gap-cortex-12 overflow-hidden">
          <div className="flex-1 space-y-cortex-12 overflow-y-auto pr-1">
            {activeSession?.messages?.map((message, index) => (
              <MessageCard
                key={`${activeSession.id}-${index}-${message.role}-${message.pending ? "pending" : "done"}`}
                message={message}
              />
            ))}
            {loading ? (
              <div className="flex justify-start">
                <div className="rounded-cortex-lg border border-cortex-border bg-cortex-surface px-cortex-16 py-cortex-12 backdrop-blur-xl">
                  <div className="flex items-center gap-cortex-12">
                    <Loader />
                    <span className="font-mono text-sm text-cortex-text-muted">Cortex processing...</span>
                  </div>
                </div>
              </div>
            ) : null}
            <div ref={endRef} />
          </div>

          <div className="rounded-cortex-lg border border-cortex-border bg-cortex-surface p-cortex-16 backdrop-blur-xl">
            <form
              className="grid gap-cortex-12"
              onSubmit={(event) => {
                event.preventDefault();
                submitMessage();
              }}
            >
              <label className="flex items-center gap-cortex-12 font-mono text-sm text-cortex-text-muted">
                <span className="text-cortex-cyan">cortex&gt;</span>
                <Input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Enter command..."
                  className="!border-0 !bg-transparent !px-0 !py-0 font-mono text-sm shadow-none ring-0 placeholder:text-cortex-text-muted focus:!ring-0"
                />
              </label>

              <div className="flex items-center justify-between gap-cortex-12">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                  command input
                </span>
                <div className="flex items-center gap-cortex-12">
                  <Button variant="secondary" size="sm" type="button" onClick={startNewSession}>
                    New Session
                  </Button>
                  <Button variant="primary" size="sm" type="submit" disabled={loading}>
                    Execute
                  </Button>
                </div>
              </div>
            </form>
          </div>

          {error ? (
            <div className="rounded-cortex-lg border border-cortex-error/45 bg-cortex-error/10 p-cortex-16 font-mono text-sm text-cortex-error shadow-none">
              {error}
            </div>
          ) : null}
        </div>
      </Card>

      <aside className="order-1 grid gap-cortex-16 xl:order-2">
        <Card>
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                Sessions
              </p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Grouped by session</h2>
            </div>
            <Badge variant="neutral">{sessions.length} open</Badge>
          </div>

          <div className="mt-cortex-16 grid gap-cortex-8">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => setActiveSessionId(session.id)}
                className={[
                  "flex items-center justify-between gap-cortex-12 rounded-cortex border px-cortex-12 py-cortex-12 text-left transition duration-cortex ease-cortex",
                  session.id === activeSessionId
                    ? "border-cortex-cyan/30 bg-cortex-surface text-cortex-text shadow-cortex-cyan"
                    : "border-cortex-border bg-transparent text-cortex-text-muted hover:border-cortex-border hover:bg-cortex-surface hover:text-cortex-text",
                ].join(" ")}
              >
                <div className="min-w-0">
                  <div className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                    {session.title}
                  </div>
                  <div className="truncate text-sm text-cortex-text">
                    {session.messages?.[session.messages.length - 1]?.content || "Empty session"}
                  </div>
                </div>
                <Badge variant={session.id === activeSessionId ? "cyan" : "neutral"}>
                  {session.messages?.length || 0}
                </Badge>
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between gap-cortex-12">
            <span className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
              Runtime
            </span>
            <Badge variant={loading ? "warning" : "green"}>{loading ? "busy" : "ready"}</Badge>
          </div>
          <div className="mt-cortex-12 grid gap-cortex-8">
            <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/80 px-cortex-12 py-cortex-12 font-mono text-sm text-cortex-text-muted">
              User messages align right.
            </div>
            <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/80 px-cortex-12 py-cortex-12 font-mono text-sm text-cortex-text-muted">
              Cortex responses align left in cards.
            </div>
            <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/80 px-cortex-12 py-cortex-12 font-mono text-sm text-cortex-text-muted">
              Latency is measured per response.
            </div>
          </div>
        </Card>
      </aside>
    </section>
  );
}
