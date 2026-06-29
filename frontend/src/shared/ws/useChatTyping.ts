"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "./useWebSocket";

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
 * Uses the shared useWebSocket hook for auto-reconnect.
 * Sends typing events when user types, receives typing events from others.
 */
export function useChatTyping({ conversationId, userId }: UseChatTypingOptions) {
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isTypingRef = useRef(false);
  const currentConvRef = useRef<number | null>(null);

  // Track pending join/leave for when WS reconnects
  const pendingJoinRef = useRef<number | null>(null);

  const handleWSMessage = useCallback(
    (data: Record<string, unknown>) => {
      if (
        data.type === "typing" &&
        data.user_id !== userId &&
        typeof data.user_id === "number" &&
        typeof data.conversation_id === "number"
      ) {
        const uid = data.user_id;
        const cid = data.conversation_id;
        setTypingUsers((prev) => {
          if (prev.some((u) => u.userId === uid && u.conversationId === cid)) {
            return prev;
          }
          return [...prev, { userId: uid, conversationId: cid }];
        });
        // Auto-remove after 5 seconds
        setTimeout(() => {
          setTypingUsers((prev) =>
            prev.filter((u) => !(u.userId === uid && u.conversationId === cid)),
          );
        }, 5000);
      } else if (
        data.type === "stop_typing" &&
        data.user_id !== userId &&
        typeof data.user_id === "number" &&
        typeof data.conversation_id === "number"
      ) {
        const uid = data.user_id;
        const cid = data.conversation_id;
        setTypingUsers((prev) =>
          prev.filter((u) => !(u.userId === uid && u.conversationId === cid)),
        );
      }
    },
    [userId],
  );

  const { send, status } = useWebSocket({
    path: "/api/v1/ws/chat",
    enabled: !!userId,
    onMessage: handleWSMessage,
  });

  // Join/leave conversation on connect and conversationId change
  useEffect(() => {
    if (status !== "connected") return;

    if (currentConvRef.current !== null) {
      send({ action: "leave", conversation_id: currentConvRef.current });
    }

    if (conversationId !== null) {
      send({ action: "join", conversation_id: conversationId });
      currentConvRef.current = conversationId;
    } else {
      currentConvRef.current = null;
    }
  }, [conversationId, status, send]);

  // Send typing indicator
  const sendTyping = useCallback(() => {
    if (status !== "connected" || !conversationId) return;

    if (!isTypingRef.current) {
      isTypingRef.current = true;
      send({ action: "typing", conversation_id: conversationId });
    }

    // Reset the stop_typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      isTypingRef.current = false;
      send({ action: "stop_typing", conversation_id: conversationId });
    }, 3000);
  }, [conversationId, status, send]);

  // Others typing in this conversation
  const isOthersTyping = typingUsers.filter((u) => u.conversationId === conversationId);

  return {
    sendTyping,
    isOthersTyping: isOthersTyping.length > 0,
    typingCount: isOthersTyping.length,
  };
}
