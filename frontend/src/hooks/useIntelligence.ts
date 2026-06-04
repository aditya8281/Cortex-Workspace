import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getAutomationSettings,
  getLatestSyncRun,
  getProactiveNotifications,
  getSyncStatus,
  listRepositoryProfiles,
  triggerSyncNow,
  updateAutomationSettings,
  pauseSync,
  resumeSync,
  cancelSync,
  forceResync,
  getScopeConfig,
  addIncludeFolder,
  addExcludeFolder,
  removeIncludeFolder,
  removeExcludeFolder,
} from "@/api/intelligence";
import { getWorkspaceIntelligence } from "@/api/ai";

export const intelligenceKeys = {
  status: ["sync", "status"] as const,
  latestRun: ["sync", "latest"] as const,
  repos: ["repos"] as const,
  proactive: ["proactive"] as const,
  automation: ["automation"] as const,
  workspace: ["workspace"] as const,
};

export function useSyncStatus() {
  return useQuery({
    queryKey: intelligenceKeys.status,
    queryFn: getSyncStatus,
    refetchInterval: 5000,
    retry: false,
  });
}

export function useLatestSyncRun() {
  return useQuery({ queryKey: intelligenceKeys.latestRun, queryFn: getLatestSyncRun });
}

export function useRepositoryProfiles() {
  return useQuery({ queryKey: intelligenceKeys.repos, queryFn: listRepositoryProfiles });
}

export function useProactiveNotifications() {
  return useQuery({ queryKey: intelligenceKeys.proactive, queryFn: getProactiveNotifications });
}

export function useAutomationSettings() {
  return useQuery({ queryKey: intelligenceKeys.automation, queryFn: getAutomationSettings });
}

export function useWorkspaceIntelligence() {
  return useQuery({
    queryKey: intelligenceKeys.workspace,
    queryFn: getWorkspaceIntelligence,
    retry: false,
  });
}

export function useTriggerSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: triggerSyncNow,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: intelligenceKeys.status });
      void qc.invalidateQueries({ queryKey: intelligenceKeys.latestRun });
      void qc.invalidateQueries({ queryKey: intelligenceKeys.repos });
    },
  });
}

export function useUpdateAutomation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: updateAutomationSettings,
    onSuccess: () => void qc.invalidateQueries({ queryKey: intelligenceKeys.automation }),
  });
}

export const scopeKeys = {
  config: ["sync", "config"] as const,
};

export function useScopeConfig() {
  return useQuery({
    queryKey: scopeKeys.config,
    queryFn: getScopeConfig,
  });
}

export function useAddIncludeFolder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: addIncludeFolder,
    onSuccess: () => void qc.invalidateQueries({ queryKey: scopeKeys.config }),
  });
}

export function useAddExcludeFolder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: addExcludeFolder,
    onSuccess: () => void qc.invalidateQueries({ queryKey: scopeKeys.config }),
  });
}

export function useRemoveIncludeFolder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: removeIncludeFolder,
    onSuccess: () => void qc.invalidateQueries({ queryKey: scopeKeys.config }),
  });
}

export function useRemoveExcludeFolder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: removeExcludeFolder,
    onSuccess: () => void qc.invalidateQueries({ queryKey: scopeKeys.config }),
  });
}

export function usePauseSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: pauseSync,
    onSuccess: () => void qc.invalidateQueries({ queryKey: intelligenceKeys.status }),
  });
}

export function useResumeSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: resumeSync,
    onSuccess: () => void qc.invalidateQueries({ queryKey: intelligenceKeys.status }),
  });
}

export function useCancelSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: cancelSync,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: intelligenceKeys.status });
      void qc.invalidateQueries({ queryKey: intelligenceKeys.latestRun });
    },
  });
}

export function useForceResync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: forceResync,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: intelligenceKeys.status });
      void qc.invalidateQueries({ queryKey: intelligenceKeys.latestRun });
    },
  });
}
