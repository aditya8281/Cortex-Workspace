/**
 * Search API client (placeholder for Phase 3).
 */

import { api } from "./client";

export const searchApi = {
  unified: (query: string, params?: { repo_id?: number; node_type?: string; max_results?: number }): Promise<any[]> => {
    const searchParams = new URLSearchParams({ q: query });
    if (params?.repo_id) searchParams.set("repo_id", String(params.repo_id));
    if (params?.node_type) searchParams.set("node_type", params.node_type);
    if (params?.max_results) searchParams.set("max_results", String(params.max_results));
    return api.get(`/api/v1/search/?${searchParams.toString()}`);
  },
};
