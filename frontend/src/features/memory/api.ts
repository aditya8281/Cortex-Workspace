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
  user_id: number;
  content: string;
  context: Record<string, any> | null;
  emotion: string | null;
  importance: number;
  confidence: number;
  access_count: number;
  last_accessed: string | null;
  created_at: string;
  updated_at: string | null;
  recency_score: number;
}

export interface SemanticMemory {
  id: number;
  user_id: number;
  content: string;
  category: string | null;
  confidence: number;
  source: string | null;
  access_count: number;
  last_accessed: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface WorkingMemory {
  id: number;
  user_id: number;
  session_id: string;
  content: string;
  slot: string;
  priority: number;
  created_at: string;
  expires_at: string;
}

export interface MemoryNode {
  id: number;
  user_id: number;
  memory_type: string;
  memory_id: number;
  label: string;
  embedding_id: string | null;
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
  nodes_by_type: Record<string, number>;
  avg_edge_weight: number;
  strongest_connections: MemoryEdge[];
}

export interface SearchResult {
  content: string;
  source: string;
  score: number;
  file_path: string;
  document_id: number | null;
  language: string | null;
  chunk_type: string | null;
}

export interface KnowledgeHealth {
  status: string;
  documents_indexed: number;
  total_chunks: number;
  graph_nodes: number;
  graph_edges: number;
  repos_indexed: number;
  code_chunks: number;
}

export interface KnowledgeStats {
  documents_by_type: Record<string, number>;
  chunks_by_language: Record<string, number>;
  avg_chunks_per_document: number;
  graph_edge_types: Record<string, number>;
}

export interface LTMEntry {
  id: number;
  category: string;
  title: string;
  content: string;
  confidence: number;
  access_count: number;
  source: string | null;
  created_at: string | null;
}

// ── Episodic Memory ────────────────────────────────────────────────────────

export const episodicMemory = {
  list: (params?: { limit?: number; offset?: number }) =>
    apiFetch<{ memories: EpisodicMemory[]; total: number; page: number; page_size: number }>(
      `/memory/episodic${params ? `?limit=${params.limit ?? 10}&offset=${params.offset ?? 0}` : ""}`,
    ),

  create: (data: { content: string; context?: Record<string, any>; emotion?: string; importance?: number }) =>
    apiFetch<EpisodicMemory>("/memory/episodic", { method: "POST", body: data }),

  get: (id: number) =>
    apiFetch<EpisodicMemory>(`/memory/episodic/${id}`),

  search: (params: { query: string; limit?: number }) =>
    apiFetch<{ results: EpisodicMemory[]; query: string; count: number }>(
      `/memory/episodic/search?query=${encodeURIComponent(params.query)}&limit=${params.limit ?? 10}`,
    ),

  delete: (id: number) =>
    apiFetch<void>(`/memory/episodic/${id}`, { method: "DELETE" }),
};

// ── Semantic Memory ────────────────────────────────────────────────────────

export const semanticMemory = {
  list: (params?: { limit?: number; offset?: number; category?: string }) =>
    apiFetch<{ memories: SemanticMemory[]; total: number; page: number; page_size: number }>(
      `/memory/semantic${params ? `?limit=${params.limit ?? 50}&offset=${params.offset ?? 0}${params.category ? `&category=${encodeURIComponent(params.category)}` : ""}` : ""}`,
    ),

  create: (data: { content: string; category?: string; source?: string }) =>
    apiFetch<SemanticMemory>("/memory/semantic", { method: "POST", body: data }),

  get: (id: number) =>
    apiFetch<SemanticMemory>(`/memory/semantic/${id}`),

  categories: () =>
    apiFetch<Array<{ category: string; count: number }>>("/memory/semantic/categories"),

  search: (params: { query: string; limit?: number }) =>
    apiFetch<{ results: SemanticMemory[]; query: string; count: number }>(
      `/memory/semantic/search?query=${encodeURIComponent(params.query)}&limit=${params.limit ?? 10}`,
    ),

  delete: (id: number) =>
    apiFetch<void>(`/memory/semantic/${id}`, { method: "DELETE" }),
};

// ── Working Memory ─────────────────────────────────────────────────────────

export const workingMemory = {
  list: (sessionId: string, slot?: string) =>
    apiFetch<{ memories: WorkingMemory[]; total: number }>(
      `/memory/working?session_id=${encodeURIComponent(sessionId)}${slot ? `&slot=${encodeURIComponent(slot)}` : ""}`,
    ),

  create: (data: { content: string; session_id: string; slot?: string; priority?: number }) =>
    apiFetch<WorkingMemory>("/memory/working", { method: "POST", body: data }),

  promote: (id: number) =>
    apiFetch<{ promoted: boolean }>(`/memory/working/${id}/promote`, { method: "POST" }),

  archive: (id: number) =>
    apiFetch<{ archived: boolean }>(`/memory/working/${id}/archive`, { method: "POST" }),

  demote: (id: number) =>
    apiFetch<{ demoted: boolean }>(`/memory/working/${id}/demote`, { method: "POST" }),

  delete: (id: number) =>
    apiFetch<void>(`/memory/working/${id}`, { method: "DELETE" }),

  deleteSession: (sessionId: string) =>
    apiFetch<{ cleared: number }>(`/memory/working/session/${sessionId}`, { method: "DELETE" }),

  sessionSummary: (sessionId: string) =>
    apiFetch<Record<string, any>>(`/memory/working/session/${sessionId}/summary`),
};

// ── Memory Graph ───────────────────────────────────────────────────────────

export const memoryGraph = {
  stats: () =>
    apiFetch<GraphStats>("/memory/graph/stats"),

  strongest: (params?: { limit?: number }) =>
    apiFetch<MemoryEdge[]>(`/memory/graph/strongest${params?.limit ? `?limit=${params.limit}` : ""}`),

  addNode: (data: { memory_id: number; memory_type: string; label: string }) =>
    apiFetch<MemoryNode>("/memory/graph/node", { method: "POST", body: data }),

  nodeConnections: (nodeId: number) =>
    apiFetch<{ node_id: number; depth: number; connections: any[] }>(`/memory/graph/node/${nodeId}/connections`),

  findPath: (sourceId: number, targetId: number) =>
    apiFetch<{ path: MemoryNode[]; length: number }>(`/memory/graph/path/${sourceId}/${targetId}`),

  addEdge: (data: { source_id: number; target_id: number; edge_type: string; weight?: number }) =>
    apiFetch<MemoryEdge>("/memory/graph/edge", { method: "POST", body: data }),

  strengthenEdge: (edgeId: number) =>
    apiFetch<MemoryEdge>(`/memory/graph/edge/${edgeId}/strengthen`, { method: "POST" }),

  deleteEdge: (edgeId: number) =>
    apiFetch<void>(`/memory/graph/edge/${edgeId}`, { method: "DELETE" }),
};

// ── Memory Search ──────────────────────────────────────────────────────────

export const memorySearch = {
  search: (params: { query: string; repo_id?: number; max_results?: number; cursor?: string }) => {
    const searchParams = new URLSearchParams({ query: params.query });
    if (params.repo_id) searchParams.set("repo_id", String(params.repo_id));
    if (params.max_results) searchParams.set("max_results", String(params.max_results));
    if (params.cursor) searchParams.set("cursor", params.cursor);
    return apiFetch<{ results: SearchResult[]; total: number; query: string; next_cursor: string | null; has_more: boolean }>(
      `/memory/search?${searchParams}`,
    );
  },

  postSearch: (data: { query: string; repo_id?: number; max_results?: number; sources?: string[]; diversity?: number; cursor?: string }) =>
    apiFetch<{ results: SearchResult[]; total: number; query: string; next_cursor: string | null; has_more: boolean }>(
      "/memory/search", { method: "POST", body: data },
    ),

  answer: (data: { query: string; repo_id?: number; max_results?: number }) =>
    apiFetch<{ query: string; answer: string; results: SearchResult[] }>("/memory/search/answer", { method: "POST", body: data }),
};

// ── Cortex Search ──────────────────────────────────────────────────────────

export const cortexSearch = {
  search: (params: { query: string; memory_type?: string; limit?: number; min_score?: number }) => {
    const searchParams = new URLSearchParams({ query: params.query });
    if (params.memory_type) searchParams.set("memory_type", params.memory_type);
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.min_score) searchParams.set("min_score", String(params.min_score));
    return apiFetch<{ results: any[]; query: string; count: number }>(
      `/memory/cortex-search?${searchParams}`,
    );
  },

  related: (params: { memory_type: string; memory_id: number; limit?: number }) => {
    const searchParams = new URLSearchParams({
      memory_type: params.memory_type,
      memory_id: String(params.memory_id),
    });
    if (params.limit) searchParams.set("limit", String(params.limit));
    return apiFetch<{ related: any[]; count: number }>(
      `/memory/cortex-search/related?${searchParams}`,
    );
  },

  byImportance: (params?: { min_importance?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.min_importance) searchParams.set("min_importance", String(params.min_importance));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return apiFetch<any[]>(`/memory/cortex-search/importance${qs ? `?${qs}` : ""}`);
  },

  byRecency: (params?: { limit?: number }) =>
    apiFetch<any[]>(`/memory/cortex-search/recency${params?.limit ? `?limit=${params.limit}` : ""}`),
};

// ── Forgetting ─────────────────────────────────────────────────────────────

export const memoryForget = {
  forget: () =>
    apiFetch<Record<string, any>>("/memory/forget", { method: "POST" }),

  stats: () =>
    apiFetch<Record<string, any>>("/memory/forget/stats"),
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
  list: (params?: { category?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set("category", params.category);
    const qs = searchParams.toString();
    return apiFetch<{ memories: LTMEntry[] | null; grouped: Record<string, LTMEntry[]> | null }>(
      `/memory/long-term-memory${qs ? `?${qs}` : ""}`,
    );
  },

  stats: () =>
    apiFetch<{ total: number; active: number; by_category: Record<string, number>; avg_confidence: number }>(
      "/memory/long-term-memory/stats",
    ),

  create: (data: { category: string; title: string; content: string; source?: string; source_id?: number; tags?: string[] }) =>
    apiFetch<{ id: number; status: string }>("/memory/long-term-memory", { method: "POST", body: data }),

  reinforce: (id: number) =>
    apiFetch<{ confidence: number }>(`/memory/long-term-memory/${id}/reinforce`, { method: "POST" }),

  delete: (id: number) =>
    apiFetch<{ status: string }>(`/memory/long-term-memory/${id}`, { method: "DELETE" }),
};
