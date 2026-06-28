/**
 * Memory API Client — v1.03 Memory Foundation
 *
 * Covers: Episodic, Semantic, Working memory, Graph, Search, Knowledge, LTM, Forget
 * Backend routes: /api/v1/memory/*
 */
import { apiFetch } from "@/shared/api/client";

// ── Types ──────────────────────────────────────────────────────────────────

export interface EpisodicMemory {
  id: number;
  content: string;
  emotion_tags: string[];
  importance: number;
  confidence: number;
  access_count: number;
  created_at: string;
  last_accessed: string;
  user_id: number;
}

export interface SemanticMemory {
  id: number;
  content: string;
  category: string;
  source: string;
  confidence: number;
  access_count: number;
  created_at: string;
  user_id: number;
}

export interface WorkingMemory {
  id: number;
  content: string;
  slot: "active" | "buffer" | "archive";
  session_id: string;
  priority: number;
  created_at: string;
  user_id: number;
}

export interface MemoryNode {
  id: number;
  memory_id: number;
  memory_type: string;
  label: string;
  importance: number;
  created_at: string;
}

export interface MemoryEdge {
  id: number;
  source_id: number;
  target_id: number;
  edge_type: string;
  weight: number;
  created_at: string;
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  edge_types: Record<string, number>;
  density: number;
}

export interface SearchResult {
  id: number;
  content: string;
  memory_type: string;
  score: number;
  importance: number;
  recency: number;
}

export interface KnowledgeHealth {
  status: string;
  total_knowledge: number;
  last_sync: string;
}

export interface KnowledgeStats {
  total_entries: number;
  categories: Record<string, number>;
  avg_confidence: number;
}

export interface LTMEntry {
  id: number;
  content: string;
  category: string;
  strength: number;
  access_count: number;
  created_at: string;
  reinforced_at: string;
}

// ── Episodic Memory ────────────────────────────────────────────────────────

export const episodicMemory = {
  list: (params?: { limit?: number; offset?: number }) =>
    apiFetch<{ items: EpisodicMemory[]; total: number }>("/memory/episodic", { method: "GET" }),

  create: (data: { content: string; emotion_tags?: string[]; importance?: number }) =>
    apiFetch<EpisodicMemory>("/memory/episodic", { method: "POST", body: data }),

  get: (id: number) =>
    apiFetch<EpisodicMemory>(`/memory/episodic/${id}`),

  search: (params: { query: string; limit?: number }) =>
    apiFetch<{ items: EpisodicMemory[]; total: number }>(`/memory/episodic/search?query=${encodeURIComponent(params.query)}&limit=${params.limit ?? 10}`),

  delete: (id: number) =>
    apiFetch<void>(`/memory/episodic/${id}`, { method: "DELETE" }),
};

// ── Semantic Memory ────────────────────────────────────────────────────────

export const semanticMemory = {
  list: (params?: { limit?: number; offset?: number }) =>
    apiFetch<{ items: SemanticMemory[]; total: number }>("/memory/semantic", { method: "GET" }),

  create: (data: { content: string; category?: string; source?: string }) =>
    apiFetch<SemanticMemory>("/memory/semantic", { method: "POST", body: data }),

  get: (id: number) =>
    apiFetch<SemanticMemory>(`/memory/semantic/${id}`),

  categories: () =>
    apiFetch<{ categories: string[] }>("/memory/semantic/categories"),

  search: (params: { query: string; limit?: number }) =>
    apiFetch<{ items: SemanticMemory[]; total: number }>(`/memory/semantic/search?query=${encodeURIComponent(params.query)}&limit=${params.limit ?? 10}`),

  delete: (id: number) =>
    apiFetch<void>(`/memory/semantic/${id}`, { method: "DELETE" }),
};

// ── Working Memory ─────────────────────────────────────────────────────────

export const workingMemory = {
  list: (sessionId?: string) =>
    apiFetch<{ items: WorkingMemory[]; total: number }>(
      sessionId ? `/memory/working?session_id=${sessionId}` : "/memory/working",
    ),

  create: (data: { content: string; slot?: string; session_id?: string }) =>
    apiFetch<WorkingMemory>("/memory/working", { method: "POST", body: data }),

  promote: (id: number) =>
    apiFetch<void>(`/memory/working/${id}/promote`, { method: "POST" }),

  archive: (id: number) =>
    apiFetch<void>(`/memory/working/${id}/archive`, { method: "POST" }),

  demote: (id: number) =>
    apiFetch<void>(`/memory/working/${id}/demote`, { method: "POST" }),

  delete: (id: number) =>
    apiFetch<void>(`/memory/working/${id}`, { method: "DELETE" }),

  deleteSession: (sessionId: string) =>
    apiFetch<void>(`/memory/working/session/${sessionId}`, { method: "DELETE" }),

  sessionSummary: (sessionId: string) =>
    apiFetch<{ summary: string }>(`/memory/working/session/${sessionId}/summary`),
};

// ── Memory Graph ───────────────────────────────────────────────────────────

export const memoryGraph = {
  stats: () =>
    apiFetch<GraphStats>("/memory/graph/stats"),

  strongest: (params?: { limit?: number }) =>
    apiFetch<{ items: MemoryEdge[] }>(`/memory/graph/strongest${params?.limit ? `?limit=${params.limit}` : ""}`),

  addNode: (data: { memory_id: number; memory_type: string; label: string }) =>
    apiFetch<MemoryNode>("/memory/graph/node", { method: "POST", body: data }),

  nodeConnections: (nodeId: number) =>
    apiFetch<{ items: MemoryEdge[] }>(`/memory/graph/node/${nodeId}/connections`),

  findPath: (sourceId: number, targetId: number) =>
    apiFetch<{ path: MemoryNode[] }>(`/memory/graph/path/${sourceId}/${targetId}`),

  addEdge: (data: { source_id: number; target_id: number; edge_type: string; weight?: number }) =>
    apiFetch<MemoryEdge>("/memory/graph/edge", { method: "POST", body: data }),

  strengthenEdge: (edgeId: number) =>
    apiFetch<MemoryEdge>(`/memory/graph/edge/${edgeId}/strengthen`, { method: "POST" }),

  deleteEdge: (edgeId: number) =>
    apiFetch<void>(`/memory/graph/edge/${edgeId}`, { method: "DELETE" }),
};

// ── Memory Search ──────────────────────────────────────────────────────────

export const memorySearch = {
  search: (params: { query: string; types?: string[]; limit?: number }) => {
    const searchParams = new URLSearchParams({ query: params.query });
    if (params.types) searchParams.set("types", params.types.join(","));
    if (params.limit) searchParams.set("limit", String(params.limit));
    return apiFetch<{ items: SearchResult[]; total: number }>(`/memory/search?${searchParams}`);
  },

  postSearch: (data: { query: string; types?: string[]; limit?: number }) =>
    apiFetch<{ items: SearchResult[]; total: number }>("/memory/search", { method: "POST", body: data }),

  answer: (data: { query: string }) =>
    apiFetch<{ answer: string; sources: SearchResult[] }>("/memory/search/answer", { method: "POST", body: data }),
};

// ── Cortex Search ──────────────────────────────────────────────────────────

export const cortexSearch = {
  search: (params: { query: string; limit?: number }) =>
    apiFetch<{ items: any[] }>(`/memory/cortex-search?query=${encodeURIComponent(params.query)}${params.limit ? `&limit=${params.limit}` : ""}`),

  related: (params: { memory_id: number; limit?: number }) =>
    apiFetch<{ items: any[] }>(`/memory/cortex-search/related?memory_id=${params.memory_id}${params.limit ? `&limit=${params.limit}` : ""}`),

  byImportance: (params?: { limit?: number }) =>
    apiFetch<{ items: any[] }>(`/memory/cortex-search/importance${params?.limit ? `?limit=${params.limit}` : ""}`),

  byRecency: (params?: { limit?: number }) =>
    apiFetch<{ items: any[] }>(`/memory/cortex-search/recency${params?.limit ? `?limit=${params.limit}` : ""}`),
};

// ── Forgetting ─────────────────────────────────────────────────────────────

export const memoryForget = {
  forget: (data: { memory_ids?: number[]; older_than_days?: number; below_confidence?: number }) =>
    apiFetch<{ forgotten: number }>("/memory/forget", { method: "POST", body: data }),

  stats: () =>
    apiFetch<{ total: number; forgotten: number; remaining: number }>("/memory/forget/stats"),
};

// ── Knowledge ──────────────────────────────────────────────────────────────

export const knowledge = {
  health: () =>
    apiFetch<KnowledgeHealth>("/memory/knowledge/health"),

  stats: () =>
    apiFetch<KnowledgeStats>("/memory/knowledge/stats"),

  retrievalMetrics: () =>
    apiFetch<any>("/memory/knowledge/retrieval-metrics"),
};

// ── Long-Term Memory ───────────────────────────────────────────────────────

export const longTermMemory = {
  list: (params?: { limit?: number; offset?: number; category?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    if (params?.category) searchParams.set("category", params.category);
    const qs = searchParams.toString();
    return apiFetch<{ items: LTMEntry[]; total: number }>(`/memory/long-term-memory${qs ? `?${qs}` : ""}`);
  },

  stats: () =>
    apiFetch<{ total: number; by_category: Record<string, number>; avg_strength: number }>("/memory/long-term-memory/stats"),

  create: (data: { content: string; category?: string }) =>
    apiFetch<LTMEntry>("/memory/long-term-memory", { method: "POST", body: data }),

  reinforce: (id: number) =>
    apiFetch<{ strength: number }>(`/memory/long-term-memory/${id}/reinforce`, { method: "POST" }),

  delete: (id: number) =>
    apiFetch<void>(`/memory/long-term-memory/${id}`, { method: "DELETE" }),
};
