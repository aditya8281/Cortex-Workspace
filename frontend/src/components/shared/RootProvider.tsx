"use client";

import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { useAuth } from "@/hooks/useAuth";
import { setUser } from "@/state/slices/auth";

export function RootProvider({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();
  const { checkAuth } = useAuth();

  useEffect(() => {
    // Check if user is already logged in on mount
    checkAuth();
  }, [checkAuth]);

  return <>{children}</>;
}
