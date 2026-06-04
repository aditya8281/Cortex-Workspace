"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Card, Button } from "@/components/ui/base";

interface NotFoundProps {
  title?: string;
  message?: string;
}

export function NotFound({ title = "Page Not Found", message = "The page you're looking for doesn't exist." }: NotFoundProps) {
  const router = useRouter();

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="max-w-md text-center">
        <h1 className="text-4xl font-bold text-primary mb-2">404</h1>
        <h2 className="text-xl font-bold mb-2">{title}</h2>
        <p className="text-gray-400 mb-6">{message}</p>
        <Button onClick={() => router.push("/dashboard")}>Back to Dashboard</Button>
      </Card>
    </div>
  );
}
