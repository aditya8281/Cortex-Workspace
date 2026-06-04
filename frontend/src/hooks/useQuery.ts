import { useState, useCallback, useEffect, useRef } from "react";

interface UseQueryOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

interface UseQueryResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useQuery<T>(
  fetchFn: () => Promise<T>,
  options?: UseQueryOptions
): UseQueryResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const fetchFnRef = useRef(fetchFn);

  useEffect(() => {
    fetchFnRef.current = fetchFn;
  }, [fetchFn]);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFnRef.current();
      setData(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error("Query error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (options?.enabled === false) return;
    fetch();

    if (options?.refetchInterval) {
      const interval = setInterval(fetch, options.refetchInterval);
      return () => clearInterval(interval);
    }
  }, [fetch, options]);

  return { data, loading, error, refetch: fetch };
}

interface UseMutationResult<T> {
  mutate: <V = unknown>(data?: V) => Promise<T>;
  loading: boolean;
  error: Error | null;
  success: boolean;
}

export function useMutation<T>(
  mutationFn: <V = unknown>(data?: V) => Promise<T>
): UseMutationResult<T> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [success, setSuccess] = useState(false);

  const mutate = useCallback(
    async <V = unknown>(data?: V) => {
      try {
        setLoading(true);
        setError(null);
        setSuccess(false);
        const result = await mutationFn(data);
        setSuccess(true);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        console.error("Mutation error:", err);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [mutationFn]
  );

  return { mutate, loading, error, success };
}
