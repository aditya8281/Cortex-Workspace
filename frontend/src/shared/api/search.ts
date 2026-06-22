/**
 * Search API client — unified code + memory search.
 */

import { api } from "./client";
import type { SearchResponse, SearchAnswerResponse, GraphData, NodeContext } from "../types";

export const searchApi = {
  /** Unified search across code and memory. */
  unified: (
    query: string,
    params?: {
      repo_id?: number;
      node_type?: string;
      language?: string;
      max_results?: number;
      cursor?: string;
    },
  ): Promise<SearchResponse> => {
    const searchParams = new URLSearchParams({ query });
    if (params?.repo_id) searchParams.set("repo_id", String(params.repo_id));
    if (params?.node_type) searchParams.set("node_type", params.node_type);
    if (params?.language) searchParams.set("language", params.language);
    if (params?.max_results) searchParams.set("max_results", String(params.max_results));
    if (params?.cursor) searchParams.set("cursor", params.cursor);
    return api.get(`/api/v1/search?${searchParams.toString()}`);
  },

  /** POST variant for complex queries. */
  unifiedPost: (body: {
    query: string;
    repo_id?: number;
    node_type?: string;
    language?: string;
    max_results?: number;
  }): Promise<SearchResponse> => {
    return api.post("/api/v1/search", body);
  },

  /** Get graph for a repository. */
  getGraph: (repoId: number): Promise<GraphData> => {
    return api.get(`/api/v1/repos/${repoId}/graph`);
  },

  /** Get context for a specific graph node. */
  getNodeContext: (repoId: number, nodeId: number): Promise<NodeContext> => {
    return api.get(`/api/v1/repos/${repoId}/graph/node/${nodeId}`);
  },

  /** Search and get an LLM-synthesized answer. */
  answer: (
    query: string,
    params?: { repo_id?: number; max_results?: number },
  ): Promise<SearchAnswerResponse> => {
    return api.post("/api/v1/search/answer", {
      query,
      repo_id: params?.repo_id,
      max_results: params?.max_results,
    });
  },
};
