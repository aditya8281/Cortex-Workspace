"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ── Types ──────────────────────────────────────────────────────────────────

export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

export interface UseWebSocketOptions {
  /** Backend path (e.g. "/api/v1/ws/system"). Used as-is against ws://host:8000 */
  path: string;
  /** Auto-reconnect on disconnect. Default: true */
  autoReconnect?: boolean;
  /** Max reconnect attempts. Default: 10 */
  maxRetries?: number;
  /** Enable the connection. Default: true */
  enabled?: boolean;
  /** Callback for each incoming message */
  onMessage?: (data: Record<string, unknown>) => void;
  /** Callback when connection opens */
  onOpen?: () => void;
  /** Callback when connection closes */
  onClose?: () => void;
  /** Callback on error */
  onError?: (error: Event) => void;
}

export interface UseWebSocketReturn {
  /** Current connection status */
  status: WSStatus;
  /** Send a JSON message to the server */
  send: (data: Record<string, unknown>) => void;
  /** Manually reconnect */
  reconnect: () => void;
  /** Manually disconnect */
  disconnect: () => void;
  /** Last received message */
  lastMessage: Record<string, unknown> | null;
}

// ── Constants ──────────────────────────────────────────────────────────────

/** Backend WebSocket base URL. WS connects directly to FastAPI (port 8000)
 *  because Next.js rewrites don't proxy WebSocket upgrades. */
function getWsBaseUrl(): string {
  if (typeof window === "undefined") return "ws://localhost:8000";
  // In dev, frontend is at :3000, backend at :8000
  return `ws://${window.location.hostname}:8000`;
}

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];

// ── Hook ───────────────────────────────────────────────────────────────────

export function useWebSocket({
  path,
  autoReconnect = true,
  maxRetries = 10,
  enabled = true,
  onMessage,
  onOpen,
  onClose,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryCount = useRef(0);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // Store callbacks in refs to avoid reconnecting on callback change
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onErrorRef = useRef(onError);
  onMessageRef.current = onMessage;
  onOpenRef.current = onOpen;
  onCloseRef.current = onClose;
  onErrorRef.current = onError;

  const cleanup = useCallback(() => {
    if (retryTimer.current) {
      clearTimeout(retryTimer.current);
      retryTimer.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent auto-reconnect on manual close
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(async () => {
    if (!enabled || !mountedRef.current) return;
    cleanup();

    setStatus("connecting");

    try {
      // Fetch access token via API (browser can't read httpOnly cookie)
      const res = await fetch("/api/v1/auth/ws-token", { credentials: "include" });
      if (!res.ok) {
        setStatus("error");
        return;
      }
      const { token } = await res.json();

      const url = `${getWsBaseUrl()}${path}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setStatus("connected");
        retryCount.current = 0;
        onOpenRef.current?.();
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          onMessageRef.current?.(data);
        } catch {
          // Non-JSON message, ignore
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setStatus("disconnected");
        onCloseRef.current?.();

        if (autoReconnect && retryCount.current < maxRetries) {
          const delay = RECONNECT_DELAYS[Math.min(retryCount.current, RECONNECT_DELAYS.length - 1)];
          retryCount.current += 1;
          retryTimer.current = setTimeout(() => {
            if (mountedRef.current) connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        setStatus("error");
        onErrorRef.current?.(error);
      };
    } catch {
      if (!mountedRef.current) return;
      setStatus("error");
    }
  }, [path, enabled, autoReconnect, maxRetries, cleanup]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const reconnect = useCallback(() => {
    retryCount.current = 0;
    connect();
  }, [connect]);

  const disconnect = useCallback(() => {
    retryCount.current = maxRetries; // prevent auto-reconnect
    cleanup();
    setStatus("disconnected");
  }, [cleanup, maxRetries]);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled) connect();

    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [enabled, connect, cleanup]);

  return { status, send, reconnect, disconnect, lastMessage };
}
