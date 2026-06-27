'use client';

import { useState, useCallback } from 'react';

interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
}

interface UsePaginationResult {
  page: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  hasPrev: boolean;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setTotal: (total: number) => void;
  nextPage: () => void;
  prevPage: () => void;
}

export function usePagination(
  options: UsePaginationOptions = {}
): UsePaginationResult {
  const { initialPage = 1, initialPageSize = 20 } = options;
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [total, setTotal] = useState(0);

  const hasNext = page * pageSize < total;
  const hasPrev = page > 1;

  const nextPage = useCallback(() => {
    if (hasNext) setPage(p => p + 1);
  }, [hasNext]);

  const prevPage = useCallback(() => {
    if (hasPrev) setPage(p => p - 1);
  }, [hasPrev]);

  return { page, pageSize, total, hasNext, hasPrev, setPage, setPageSize, setTotal, nextPage, prevPage };
}
