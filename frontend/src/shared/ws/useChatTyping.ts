"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface TypingUser {
  userId: number;
  conversationId: number;
}

interface UseChatTypingOptions {
  conversationId: number | null;
  userId: number | undefined;
}

/**
 * Hook for chat typing indicators via WebSocket.
 * Sends typing events when user types, receives typing events from others.
 */
export function useChatTyping({ conversationId, userId }: UseChatTypingOptions) {
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isTypingRef = useRef(false);
  const mountedRef = useRef(true);
  const currentConvRef = useRef<number | null>(null);

  // Connect to chat WS
  useEffect(() => {
    mountedRef.current = true;

    async function connect() {
      if (!userId) return;

      try {
        const res = await fetch("/api/v1/auth/ws-token", { credentials: "include" });
        if (!res.ok) return;
        const { token } = await res.json();

        const wsUrl = `ws://${window.location.hostname}:8000/api/v1/ws/chat?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          if (!mountedRef.current) return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === "typing" && data.user_id !== userId) {
              setTypingUsers((prev) => {
                if (prev.some((u) => u.userId === data.user_id && u.conversationId === data.conversation_id)) {
                  return prev;
                }
                return [...prev, { userId: data.user_id, conversationId: data.conversation_id }];
              });
              // Auto-remove after 5 seconds
              setTimeout(() => {
                setTypingUsers((prev) =>
                  prev.filter((u) => !(u.userId === data.user_id && u.conversationId === data.conversation_id)),
                );
              }, 5000);
            } else if (data.type === "stop_typing" && data.user_id !== userId) {
              setTypingUsers((prev) =>
                prev.filter((u) => !(u.userId === data.user_id && u.conversationId === data.conversation_id)),
              );
            }
          } catch {
            // ignore
          }
        };
      } catch {
        // WS connection failed, typing indicators disabled
      }
    }

    connect();

    return () => {
      mountedRef.current = false;
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [userId]);

  // Join/leave conversation channels
  useEffect(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    if (currentConvRef.current !== null) {
      ws.send(JSON.stringify({ action: "leave", conversation_id: currentConvRef.current }));
    }

    if (conversationId !== null) {
      ws.send(JSON.stringify({ action: "join", conversation_id: conversationId }));
      currentConvRef.current = conversationId;
    }
  }, [conversationId]);

  // Send typing indicator
  const sendTyping = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || !conversationId) return;

    if (!isTypingRef.current) {
      isTypingRef.current = true;
      ws.send(JSON.stringify({ action: "typing", conversation_id: conversationId }));
    }

    // Reset the stop_typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      isTypingRef.current = false;
      ws.send(JSON.stringify({ action: "stop_typing", conversation_id: conversationId }));
    }, 3000);
  }, [conversationId]);

  // Others typing in this conversation
  const isOthersTyping = typingUsers.filter((u) => u.conversationId === conversationId);

  return {
    sendTyping,
    isOthersTyping: isOthersTyping.length > 0,
    typingCount: isOthersTyping.length,
  };
}
