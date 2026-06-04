"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to chat as the main dashboard
    router.replace("/dashboard/chat");
  }, [router]);

  return <div></div>;
}
