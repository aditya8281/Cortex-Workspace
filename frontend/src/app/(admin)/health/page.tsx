"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner } from "@/components/ui/base";
import { healthService } from "@/services/api/admin";
import type { HealthStatus } from "@/types/api";

export default function HealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const data = await healthService.checkDeep();
        setHealth(data);
      } catch (err: any) {
        setError(err.message || "Failed to fetch health status");
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">System Health</h1>

      {error && <p className="text-danger">{error}</p>}

      {health && (
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-lg">Overall Status</span>
              <Badge
                variant={health.status === "ready" ? "secondary" : "danger"}
              >
                {health.status}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4 p-4 bg-background rounded">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Database</span>
                <Badge variant={health.database ? "secondary" : "danger"}>
                  {health.database ? "OK" : "ERROR"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Memory</span>
                <Badge variant={health.memory ? "secondary" : "danger"}>
                  {health.memory ? "OK" : "ERROR"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">RAG System</span>
                <Badge variant={health.rag ? "secondary" : "danger"}>
                  {health.rag ? "OK" : "ERROR"}
                </Badge>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
