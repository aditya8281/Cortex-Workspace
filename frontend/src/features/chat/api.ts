import { apiFetch, apiFetchStream, getCsrfToken } from "@/shared/api/client";

/**
 * Direct backend URL for SSE streaming.
 * Bypasses Next.js proxy which buffers the entire response.
 */
const BACKEND_URL =
  (typeof process !== "undefined" &&
    typeof (process as any).env !== "undefined" &&
    (process as any).env.NEXT_PUBLIC_CORTEX_BACKEND_URL) ||
  "http://localhost:8000";
const API_V1 = `${BACKEND_URL}/api/v1`;

export interface Conversation {
  id: number;
  title: string;
  repo_id: number | null;
  model_used: string | null;
  message_count: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  thinking_content?: string | null;
  tokens: number;
  created_at: string;
}

/** Tool call event from SSE stream */
export interface ToolCallEvent {
  type: "tool_call";
  tool: string;
  args: Record<string, string>;
}

/** Tool result event from SSE stream */
export interface ToolResultEvent {
  type: "tool_result";
  tool: string;
  result: string;
  denied?: boolean;
}

/** Tool approval request from SSE stream */
export interface ToolApprovalEvent {
  type: "tool_approval";
  tool: string;
  args: Record<string, string>;
  call_id: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface Source {
  file_path: string;
  score: number;
  content: string;
}

export const chatApi = {
  list: (limit = 50, offset = 0) =>
    apiFetch<{ conversations: Conversation[]; total: number }>(
      `/conversations?limit=${limit}&offset=${offset}`,
    ),

  get: (id: number) =>
    apiFetch<ConversationDetail>(`/conversations/${id}`),

  create: (title: string, repo_id?: number) =>
    apiFetch<Conversation>("/conversations", {
      method: "POST",
      body: { title, repo_id },
    }),

  rename: (id: number, title: string) =>
    apiFetch<{ status: string; title: string }>(`/conversations/${id}/title`, {
      method: "PATCH",
      body: { title },
    }),

  delete: (id: number) =>
    apiFetch<{ status: string }>(`/conversations/${id}`, {
      method: "DELETE",
    }),

  cancel: (id: number) =>
    apiFetch<{ status: string }>(`/conversations/${id}/cancel`, {
      method: "POST",
    }),
};

/**
 * Step 1: Tell the backend to start generating a response.
 * This returns immediately — generation runs as a background task.
 */
export async function sendMessage(
  conversationId: number,
  content: string,
  model?: string,
): Promise<{ status: string; conversation_id: number }> {
  return apiFetch(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: { content, model },
  });
}

/**
 * Step 2: Subscribe to the SSE stream for a conversation's response.
 * Can be called before, during, or after generation starts.
 * Multiple consumers can subscribe simultaneously.
 */
export async function* subscribeToStream(
  conversationId: number,
  signal?: AbortSignal,
): AsyncGenerator<{ type: string; content?: string; tokens?: number; sources?: Source[]; tool?: string; args?: Record<string, string>; result?: string; denied?: boolean; call_id?: string }> {
  // Use the Next.js route handler at /sse/... (not /api/, so it doesn't
  // match the rewrite which buffers responses). Same origin → cookies work.
  const url = `/sse/v1/conversations/${conversationId}/stream`;
  const headers: Record<string, string> = {};

  // GET doesn't strictly need CSRF, but forward it for completeness
  headers["X-CSRF-Token"] = getCsrfToken();

  const res = await fetch(url, {
    method: "GET",
    headers,
    credentials: "include",
    signal,
  });

  if (!res.ok) {
    throw new Error(`Stream subscription failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop()!;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(trimmed.slice(6));
        yield data;
        if (data.type === "done") return;
      } catch {
        // skip malformed lines
      }
    }
  }
}

/**
 * Approve or deny a tool call that requires user permission.
 */
export async function approveToolCall(
  conversationId: number,
  callId: string,
  approved: boolean,
): Promise<{ status: string }> {
  return apiFetch(`/conversations/${conversationId}/approve`, {
    method: "POST",
    body: { call_id: callId, approved },
  });
}

/**
 * Legacy wrapper for backward compatibility.
 */
export async function* streamChat(
  conversationId: number,
  content: string,
  model?: string,
  signal?: AbortSignal,
): AsyncGenerator<{ type: string; content?: string; tokens?: number; sources?: Source[]; tool?: string; args?: Record<string, string>; result?: string; denied?: boolean; call_id?: string }> {
  await sendMessage(conversationId, content, model);
  yield* subscribeToStream(conversationId, signal);
}
