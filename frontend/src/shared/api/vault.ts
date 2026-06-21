/**
 * Vault API client.
 */

import { api } from "./client";
import type { VaultStatus, VaultFileEntry, VaultUploadResult, VaultSearchResponse } from "../types";

export const vaultApi = {
  status: (): Promise<VaultStatus> => {
    return api.get("/api/v1/me/vault/status");
  },

  unlock: (password: string): Promise<{ unlocked: boolean; message: string }> => {
    return api.post("/api/v1/me/vault/unlock", { vault_password: password });
  },

  lock: (): Promise<{ locked: boolean; message: string }> => {
    return api.post("/api/v1/me/vault/lock");
  },

  listFiles: (folder = "/", recursive = false): Promise<VaultFileEntry[]> => {
    return api.get(`/api/v1/me/vault/files?folder=${encodeURIComponent(folder)}&recursive=${recursive}`);
  },

  createFolder: (folderPath: string): Promise<{ name: string; path: string }> => {
    return api.post("/api/v1/me/vault/folders", { folder_path: folderPath });
  },

  deleteFile: (filePath: string): Promise<{ deleted: boolean }> => {
    return api.delete(`/api/v1/me/vault/files/${encodeURIComponent(filePath)}`);
  },

  renameItem: (filePath: string, newName: string): Promise<{ name: string; path: string }> => {
    return api.put(`/api/v1/me/vault/files/${encodeURIComponent(filePath)}/rename`, { new_name: newName });
  },

  moveFile: (sourcePath: string, destinationFolder: string): Promise<{ name: string; path: string }> => {
    return api.post("/api/v1/me/vault/files/move", { source_path: sourcePath, destination_folder: destinationFolder });
  },

  updateMetadata: (
    filePath: string,
    payload: { favorite?: boolean; tags?: string[] },
  ): Promise<{ path: string; favorite: boolean; tags: string[] }> => {
    return api.put(`/api/v1/me/vault/files/${encodeURIComponent(filePath)}/metadata`, payload);
  },

  exportFiles: (payload: {
    paths: string[];
    destination_dir: string;
  }): Promise<{ exported: boolean; count: number }> => {
    return api.post("/api/v1/me/vault/files/export", payload);
  },

  changePassword: (payload: {
    old_password: string;
    new_password: string;
  }): Promise<{ message: string }> => {
    return api.post("/api/v1/me/vault/change-password", payload);
  },

  search: (query: string): Promise<VaultSearchResponse> => {
    return api.post("/api/v1/me/vault/search", { query });
  },
};
