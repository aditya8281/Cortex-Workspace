"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Input, Button } from "@/components/ui/base";
import { adminService } from "@/services/api/admin";
import type { APILogEntry } from "@/types/api";

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState("ALL");

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        const data = await adminService.getExecutionLogs(100);
        setLogs(data);
      } catch (error) {
        console.error("Failed to fetch logs:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const filteredLogs =
    filterLevel === "ALL" ? logs : logs.filter((log) => log.level === filterLevel);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">API Logs</h1>
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          className="bg-surface border border-border px-4 py-2 rounded text-white"
        >
          <option>ALL</option>
          <option>INFO</option>
          <option>WARN</option>
          <option>ERROR</option>
          <option>DEBUG</option>
        </select>
      </div>

      <Card>
        <div className="space-y-2 max-h-96 overflow-y-auto font-mono text-sm">
          {filteredLogs.map((log, idx) => (
            <div
              key={idx}
              className={`p-2 rounded ${
                log.level === "ERROR"
                  ? "bg-red-900/20 text-red-400"
                  : "bg-background text-gray-400"
              }`}
            >
              <p>
                <span className="text-gray-500">{log.timestamp}</span>{" "}
                <Badge
                  variant={
                    log.level === "ERROR" ? "danger" : "secondary"
                  }
                >
                  {log.level}
                </Badge>
              </p>
              <p>{log.message}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
