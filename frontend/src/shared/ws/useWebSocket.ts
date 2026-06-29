"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ── Types ──────────────────────────────────────────────────────────────────

export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

export interface UseWebSocketOptions {
  /** Backend path (e.g. "/api/v1/ws/system"). Concatenated after getWsBaseUrl(). */
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

/** Backend WebSocket base URL. Parsed from NEXT_PUBLIC_CORTEX_BACKEND_URL
 *  (set via CORTEX_BACKEND_URL in .env.local, exposed by next.config.ts).
 *  Converts http(s)://host:port → ws(s)://host:port.
 */
export function getWsBaseUrl(): string {
  // Browser: reads NEXT_PUBLIC_* var inlined by Next.js at compile time
  const rawUrl = process.env.NEXT_PUBLIC_CORTEX_BACKEND_URL;
  // SSR: reads CORTEX_BACKEND_URL directly (available in Node.js)
  const backendUrl = rawUrl || process.env.CORTEX_BACKEND_URL;
  if (backendUrl) {
    try {
      const url = new URL(backendUrl);
      const protocol = url.protocol === "https:" ? "wss:" : "ws:";
      return `${protocol}//${url.host}`;
    } catch { /* ignore bad URL */ }
  }
  return "ws://localhost:8000";
}

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];
const HEARTBEAT_MS = 30000; // send a ping every 30s to keep connection alive

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
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);
  const intentionalClose = useRef(false);

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
    intentionalClose.current = true;

    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
    if (retryTimer.current) {
      clearTimeout(retryTimer.current);
      retryTimer.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect on manual close
      wsRef.current.onerror = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback((ws: WebSocket) => {
    if (heartbeatTimer.current) clearInterval(heartbeatTimer.current);
    heartbeatTimer.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, HEARTBEAT_MS);
  }, []);

  const connect = useCallback(async () => {
    if (!enabled || !mountedRef.current) return;
    cleanup();

    intentionalClose.current = false;
    setStatus("connecting");

    const scheduleRetry = () => {
      if (!autoReconnect || retryCount.current >= maxRetries || !mountedRef.current) return;
      const delay = RECONNECT_DELAYS[Math.min(retryCount.current, RECONNECT_DELAYS.length - 1)];
      retryCount.current += 1;
      retryTimer.current = setTimeout(() => {
        if (mountedRef.current) connect();
      }, delay);
    };

    try {
      // Fetch access token via API (browser can't read httpOnly cookie)
      const res = await fetch("/api/v1/auth/ws-token", { credentials: "include" });
      if (!res.ok) {
        setStatus("error");
        scheduleRetry();
        return;
      }
      const { token } = await res.json();
      if (!token || typeof token !== "string") {
        setStatus("error");
        scheduleRetry();
        return;
      }

      const url = `${getWsBaseUrl()}${path}`;
      const ws = new WebSocket(url, [token]);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        setStatus("connected");
        retryCount.current = 0;
        startHeartbeat(ws);
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
        if (!intentionalClose.current) {
          scheduleRetry();
        }
      };

      ws.onerror = (event) => {
        if (!mountedRef.current) return;
        setStatus("error");
        onErrorRef.current?.(event);
      };
    } catch {
      if (!mountedRef.current) return;
      setStatus("error");
      scheduleRetry();
    }
  }, [path, enabled, autoReconnect, maxRetries, cleanup, startHeartbeat]);

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
