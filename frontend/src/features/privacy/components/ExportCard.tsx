"use client";

import { useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { dataExport } from "../api";

export function ExportCard() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleExport = async () => {
    setLoading(true);
    setStatus(null);

    try {
      const res = await dataExport.create({
        format: "json",
        include: ["all"],
      });

      if (res.status === "pending" || res.status === "processing") {
        setStatus("Export is being prepared. You will be notified when it is ready.");
      } else {
        setStatus("Export completed.");
      }
    } catch {
      setStatus("Export failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <h3 className="text-sm font-semibold text-text-primary mb-2">
        Export Data
      </h3>
      <p className="mb-3 text-xs text-text-secondary">
        Export all your data for backup or migration.
      </p>
      <Button
        variant="primary"
        size="sm"
        loading={loading}
        onClick={handleExport}
      >
        Export Data
      </Button>
      {status && (
        <p
          className={`mt-2 text-xs ${
            status.toLowerCase().includes("fail")
              ? "text-danger"
              : "text-text-muted"
          }`}
        >
          {status}
        </p>
      )}
    </Card>
  );
}
