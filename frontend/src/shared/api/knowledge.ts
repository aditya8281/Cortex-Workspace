import { api } from "./client";
import type { KnowledgeHealth, KnowledgeStats } from "../types";

export const knowledgeApi = {
  health: (): Promise<KnowledgeHealth> => {
    return api.get("/api/v1/knowledge/health");
  },

  stats: (): Promise<KnowledgeStats> => {
    return api.get("/api/v1/knowledge/stats");
  },
};
