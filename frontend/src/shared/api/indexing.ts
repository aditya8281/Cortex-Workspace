/**
 * Indexing configuration API client.
 */

import { api } from "./client";
import type { IndexingConfig, IndexingConfigPayload, IndexingPreview } from "../types";

export const indexingApi = {
  get: (): Promise<{ config: IndexingConfig | null; defaults: boolean }> => {
    return api.get("/api/v1/indexing/config");
  },

  update: (body: IndexingConfigPayload): Promise<{ status: string }> => {
    return api.put("/api/v1/indexing/config", body);
  },

  preview: (repoPath: string): Promise<IndexingPreview> => {
    return api.post(`/api/v1/indexing/preview?repo_path=${encodeURIComponent(repoPath)}`);
  },
};
