/**
 * Memory API client.
 */

import { api } from "./client";
import type { MemoryEntry, MemoryListResponse, MemorySearchResponse } from "../types";

export const memoryApi = {
  list: (params: { limit?: number; offset?: number; category?: string } = {}): Promise<MemoryListResponse> => {
    const query = new URLSearchParams();
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));
    if (params.category) query.set("category", params.category);
    const qs = query.toString();
    return api.get(`/api/v1/memory${qs ? `?${qs}` : ""}`);
  },

  create: (payload: {
    title: string;
    content: string;
    category?: string;
    source_path?: string;
    tags?: string[];
  }): Promise<{ status: string; entry: MemoryEntry }> => {
    return api.post("/api/v1/memory", payload);
  },

  get: (id: number): Promise<MemoryEntry> => {
    return api.get(`/api/v1/memory/${id}`);
  },

  update: (
    id: number,
    payload: {
      title?: string;
      content?: string;
      category?: string;
      source_path?: string;
      tags?: string[];
    },
  ): Promise<{ status: string; entry: MemoryEntry }> => {
    return api.put(`/api/v1/memory/${id}`, payload);
  },

  delete: (id: number): Promise<{ status: string }> => {
    return api.delete(`/api/v1/memory/${id}`);
  },

  search: (payload: {
    query: string;
    limit?: number;
  }): Promise<MemorySearchResponse> => {
    return api.post("/api/v1/memory/search", payload);
  },

  scanRepo: (repoPath: string): Promise<{ status: string; job_id: string | null }> => {
    return api.post("/api/v1/memory/scan-repo", { repo_path: repoPath });
  },
};
