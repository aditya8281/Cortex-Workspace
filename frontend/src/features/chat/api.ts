import { apiFetch } from "@/shared/api/client";

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
  tokens: number;
  created_at: string;
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
};

export async function* streamChat(
  conversationId: number,
  content: string,
  model?: string,
): AsyncGenerator<{ type: string; content?: string; tokens?: number; sources?: Source[] }> {
  const res = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ content, model }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status}`);
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
