import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export const useOllamaRegistry = () => {
  const queryClient = useQueryClient();

  // Fetch all models
  const useAllModels = () => {
    return useQuery({
      queryKey: ['ollama', 'models'],
      queryFn: async () => {
        const response = await apiClient.get('/registry/models');
        return response.data;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
    });
  };

  // Search models
  const useSearchModels = (query: string, capability?: string, family?: string, size?: string) => {
    return useQuery({
      queryKey: ['ollama', 'search', query, capability, family, size],
      queryFn: async () => {
        const params = new URLSearchParams();
        params.append('q', query);
        if (capability) params.append('capability', capability);
        if (family) params.append('family', family);
        if (size) params.append('size', size);
        
        const response = await apiClient.get(`/registry/models/search?${params.toString()}`);
        return response.data;
      },
      enabled: query.length > 0,
      staleTime: 5 * 60 * 1000,
    });
  };

  // Get models by capability
  const useModelsByCapability = (capability: string) => {
    return useQuery({
      queryKey: ['ollama', 'capability', capability],
      queryFn: async () => {
        const response = await apiClient.get(`/registry/models/by-capability/${capability}`);
        return response.data;
      },
      staleTime: 5 * 60 * 1000,
    });
  };

  // Get single model
  const useModel = (modelId: string) => {
    return useQuery({
      queryKey: ['ollama', 'model', modelId],
      queryFn: async () => {
        const response = await apiClient.get(`/registry/models/${modelId}`);
        return response.data;
      },
    });
  };

  // Get recommendations
  const useRecommendations = (task?: string) => {
    return useQuery({
      queryKey: ['ollama', 'recommendations', task],
      queryFn: async () => {
        const params = task ? `?task=${task}` : '';
        const response = await apiClient.get(`/registry/recommendations${params}`);
        return response.data;
      },
      enabled: !!task,
    });
  };

  // Get installed models
  const useInstalledModels = () => {
    return useQuery({
      queryKey: ['ollama', 'installed'],
      queryFn: async () => {
        const response = await apiClient.get('/registry/models/installed');
        return response.data;
      },
      staleTime: 1 * 60 * 1000, // 1 minute
    });
  };

  // Sync registry
  const useSyncRegistry = () => {
    return useMutation({
      mutationFn: async (forceRefresh = false) => {
        const response = await apiClient.post('/registry/sync', { force_refresh: forceRefresh });
        return response.data;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['ollama'] });
      },
    });
  };

  // Pull model
  const usePullModel = () => {
    return useMutation({
      mutationFn: async (modelId: string) => {
        const response = await apiClient.post(`/registry/models/${modelId}/pull`);
        return response.data;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['ollama', 'installed'] });
      },
    });
  };

  // Get download progress
  const useDownloadProgress = (progressId: number | null) => {
    return useQuery({
      queryKey: ['ollama', 'download', progressId],
      queryFn: async () => {
        const response = await apiClient.get(`/registry/downloads/${progressId}`);
        return response.data;
      },
      enabled: !!progressId,
      refetchInterval: 1000, // Poll every second
    });
  };

  // Mark model as installed
  const useMarkInstalled = () => {
    return useMutation({
      mutationFn: async (modelId: string) => {
        const response = await apiClient.post(`/registry/models/${modelId}/mark-installed`);
        return response.data;
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['ollama'] });
      },
    });
  };

  return {
    useAllModels,
    useSearchModels,
    useModelsByCapability,
    useModel,
    useRecommendations,
    useInstalledModels,
    useSyncRegistry,
    usePullModel,
    useDownloadProgress,
    useMarkInstalled,
  };
};
