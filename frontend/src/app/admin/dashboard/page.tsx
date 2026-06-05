"use client";

import { useState, useEffect } from "react";
import { Card, Spinner, Badge } from "@/components/ui/base";
import { adminService, healthService } from "@/services/api/admin";
import type { SystemMetrics, User } from "@/types/api";

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [metricsData, usersData] = await Promise.all([
          adminService.getMetrics(),
          adminService.listUsers(),
        ]);
        setMetrics(metricsData);
        setUsers(usersData);
      } catch (error) {
        console.error("Failed to fetch admin data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
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
      <h1 className="text-3xl font-bold">System Overview</h1>

      {/* System Metrics */}
      {metrics && (
        <Card>
          <h2 className="text-xl font-bold mb-4">System Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-400 text-sm">Availability</p>
              <p className="text-2xl font-bold">{Number(metrics.availability ?? 0).toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Avg Latency</p>
              <p className="text-2xl font-bold">{Number(metrics.avg_latency_ms ?? 0).toFixed(0)}ms</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Error Rate</p>
              <p className="text-2xl font-bold">{Number(metrics.error_rate ?? 0).toFixed(2)}%</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">CPU Usage</p>
              <p className="text-2xl font-bold">{Number(metrics.cpu_usage ?? 0).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Memory</p>
              <p className="text-2xl font-bold">{metrics.memory_usage_mb}MB</p>
            </div>
          </div>
        </Card>
      )}

      {/* Active Users */}
      <Card>
        <h2 className="text-xl font-bold mb-4">Active Users ({users.length})</h2>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {users.map((user) => (
            <div key={user.id} className="flex items-center justify-between p-2 bg-background rounded">
              <div>
                <p className="font-medium">{user.full_name}</p>
                <p className="text-sm text-gray-400">{user.email}</p>
              </div>
              <Badge variant={user.role === "admin" ? "danger" : "secondary"}>
                {user.role}
              </Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
