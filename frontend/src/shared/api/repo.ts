/**
 * Repository API client — CRUD, indexing, and graph operations.
 */

import { api } from "./client";
import type { Repository, RepoListResponse, RepoStatus, IndexResult } from "../types";

export const repoApi = {
  /** List all repositories. */
  list: (): Promise<RepoListResponse> => {
    return api.get("/api/v1/repos");
  },

  /** Create a new repository entry. */
  create: (body: {
    name: string;
    path: string;
  }): Promise<{ status: string; repo: Repository }> => {
    return api.post("/api/v1/repos", body);
  },

  /** Get a specific repository. */
  get: (repoId: number): Promise<{ repo: Repository }> => {
    return api.get(`/api/v1/repos/${repoId}`);
  },

  /** Update repository metadata. */
  update: (
    repoId: number,
    body: { name?: string },
  ): Promise<{ status: string; repo: Repository }> => {
    return api.put(`/api/v1/repos/${repoId}`, body);
  },

  /** Delete a repository. */
  delete: (repoId: number): Promise<{ status: string }> => {
    return api.delete(`/api/v1/repos/${repoId}`);
  },

  /** Trigger indexing (background by default). */
  index: (
    repoId: number,
    params?: { force?: boolean; background?: boolean },
  ): Promise<{ status: string; job_id?: string; result?: IndexResult }> => {
    const searchParams = new URLSearchParams();
    if (params?.force) searchParams.set("force", "true");
    if (params?.background === false) searchParams.set("background", "false");
    const qs = searchParams.toString();
    return api.post(`/api/v1/repos/${repoId}/index${qs ? `?${qs}` : ""}`);
  },

  /** Get indexing status. */
  status: (repoId: number): Promise<RepoStatus> => {
    return api.get(`/api/v1/repos/${repoId}/status`);
  },

  /** Build knowledge graph. */
  buildGraph: (
    repoId: number,
  ): Promise<{ status: string; nodes_created: number; edges_created: number }> => {
    return api.post(`/api/v1/repos/${repoId}/graph`);
  },
};
