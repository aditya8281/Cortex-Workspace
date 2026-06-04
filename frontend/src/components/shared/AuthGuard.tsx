import React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

interface AuthGuardProps {
  children: React.ReactNode;
  requireRole?: "user" | "admin";
}

export function AuthGuard({ children, requireRole }: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, user, loading } = useAuth();

  React.useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  if (requireRole && user?.role !== requireRole) {
    return <div className="flex items-center justify-center min-h-screen">Access Denied</div>;
  }

  return <>{children}</>;
}
