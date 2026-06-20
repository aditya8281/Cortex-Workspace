"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export type WebSocketStatus = "connecting" | "connected" | "disconnected";

interface UseSystemWebSocketOptions {
  /** WebSocket path relative to the backend root, e.g. "/ws/system" */
  path: string;
  /** Called for every message received. Return false to skip reconnect on close. */
  onMessage: (event: MessageEvent) => void;
  /** Called when connection status changes. */
  onStatusChange?: (status: WebSocketStatus) => void;
  /** Whether to connect. Default true. */
  enabled?: boolean;
}

interface UseSystemWebSocketReturn {
  /** Current connection status. */
  status: WebSocketStatus;
  /** Manually close the connection. */
  close: () => void;
  /** Manually attempt to reconnect. */
  reconnect: () => void;
}

/**
 * Reusable WebSocket hook that connects to the backend via dynamic port
 * discovery (/api/env), auto-reconnects with exponential backoff, and
 * exposes connection status.
 */
export function useSystemWebSocket({
  path,
  onMessage,
  onStatusChange,
  enabled = true,
}: UseSystemWebSocketOptions): UseSystemWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryMsRef = useRef(1000);
  const cancelledRef = useRef(false);
  const onMessageRef = useRef(onMessage);
  const onStatusChangeRef = useRef(onStatusChange);
  const pathRef = useRef(path);

  // Keep refs in sync without re-triggering the effect
  onMessageRef.current = onMessage;
  onStatusChangeRef.current = onStatusChange;
  pathRef.current = path;

  const setConnectionStatus = useCallback((s: WebSocketStatus) => {
    setStatus(s);
    onStatusChangeRef.current?.(s);
  }, []);

  const close = useCallback(() => {
    cancelledRef.current = true;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionStatus("disconnected");
  }, [setConnectionStatus]);

  const connect = useCallback(async (retryMs = 1000) => {
    if (cancelledRef.current) return;

    setConnectionStatus("connecting");

    try {
      const res = await fetch("/api/env");
      const { wsUrl } = await res.json();
      if (cancelledRef.current) return;

      const ws = new WebSocket(`${wsUrl}${pathRef.current}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (cancelledRef.current) { ws.close(); return; }
        retryMsRef.current = 1000; // reset backoff on successful connect
        setConnectionStatus("connected");
      };

      ws.onmessage = (event) => {
        onMessageRef.current(event);
      };

      ws.onerror = () => {
        // onclose will fire after this, so reconnect handling is there
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (cancelledRef.current) return;
        setConnectionStatus("disconnected");

        // Reconnect with exponential backoff (1s → 2s → 4s → … → 30s cap)
        const nextRetry = Math.min(retryMs * 2, 30000);
        retryMsRef.current = nextRetry;
        reconnectTimerRef.current = setTimeout(() => connect(nextRetry), nextRetry);
      };
    } catch {
      // Could not resolve backend URL — retry after delay
      if (cancelledRef.current) return;
      setConnectionStatus("disconnected");
      const nextRetry = Math.min(retryMs * 2, 30000);
      retryMsRef.current = nextRetry;
      reconnectTimerRef.current = setTimeout(() => connect(nextRetry), nextRetry);
    }
  }, [setConnectionStatus]);

  const reconnect = useCallback(() => {
    close();
    cancelledRef.current = false;
    retryMsRef.current = 1000;
    connect();
  }, [close, connect]);

  useEffect(() => {
    if (!enabled) return;
    cancelledRef.current = false;
    retryMsRef.current = 1000;
    connect();

    return () => {
      cancelledRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      wsRef.current?.close();
      wsRef.current = null;
      setConnectionStatus("disconnected");
    };
  }, [enabled, connect, setConnectionStatus]);

  return { status, close, reconnect };
}
