'use client';

import { useState, useEffect } from 'react';

interface AuthState {
  isAuthenticated: boolean;
  user: { id: string; email: string } | null;
  loading: boolean;
}

export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
  });

  useEffect(() => {
    // Placeholder — will use AuthProvider context in v1.03+
    setState({ isAuthenticated: false, user: null, loading: false });
  }, []);

  return state;
}
