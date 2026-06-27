'use client';

import { useState, useCallback } from 'react';
import type { ApiError } from '../types/api';

interface UseApiCallResult<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  execute: () => Promise<void>;
  refetch: () => Promise<void>;
}

export function useApiCall<T>(fn: () => Promise<T>): UseApiCallResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
    } catch (err) {
      setError({
        code: 'UNKNOWN',
        message: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  }, [fn]);

  return { data, loading, error, execute, refetch: execute };
}
