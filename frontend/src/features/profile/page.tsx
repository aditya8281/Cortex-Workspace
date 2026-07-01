"use client";

import { useEffect } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { ProfileIcon } from "@/shared/ui/icons";

export default function ProfilePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <ProfileIcon className="text-3xl" size={32} />
        <p className="mt-3 text-headline font-semibold text-text-primary">Profile</p>
        <p className="mt-1 text-sm text-text-muted">{user.username}</p>
      </div>
    </div>
  );
}
