/**
 * Conversations API client — list, create, get, delete, rename.
 */

import { api } from "./client";
import type { Conversation, ConversationDetail } from "../types";

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export const conversationsApi = {
  /** List all conversations. */
  list: async (params?: { limit?: number; offset?: number }): Promise<ConversationListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    const qs = searchParams.toString();
    return api.get(`/api/v1/conversations${qs ? `?${qs}` : ""}`);
  },

  /** Create a new conversation. */
  create: async (body: { title?: string; repo_id?: number }): Promise<Conversation> => {
    return api.post("/api/v1/conversations", body);
  },

  /** Get a conversation with messages. */
  get: async (conversationId: number): Promise<ConversationDetail> => {
    return api.get(`/api/v1/conversations/${conversationId}`);
  },

  /** Delete a conversation. */
  delete: async (conversationId: number): Promise<{ status: string }> => {
    return api.delete(`/api/v1/conversations/${conversationId}`);
  },

  /** Rename a conversation. */
  rename: async (conversationId: number, title: string): Promise<{ status: string; title: string }> => {
    return api.patch(`/api/v1/conversations/${conversationId}/title`, { title });
  },
};
