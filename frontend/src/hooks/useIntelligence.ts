import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getAutomationSettings,
  getLatestSyncRun,
  getProactiveNotifications,
  getSyncStatus,
  listRepositoryProfiles,
  triggerSyncNow,
  updateAutomationSettings,
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
  return useQuery({ queryKey: intelligenceKeys.status, queryFn: getSyncStatus, refetchInterval: 5000 });
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
  return useQuery({ queryKey: intelligenceKeys.workspace, queryFn: getWorkspaceIntelligence });
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
