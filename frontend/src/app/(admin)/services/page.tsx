"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button } from "@/components/ui/base";

export default function ServicesPage() {
  const [services, setServices] = useState<any[]>([
    { id: 1, name: "API Gateway", status: "running", uptime: "45d" },
    { id: 2, name: "RAG Engine", status: "running", uptime: "45d" },
    { id: 3, name: "Memory Vault", status: "running", uptime: "45d" },
    { id: 4, name: "Sync Engine", status: "idle", uptime: "45d" },
  ]);
  const [loading, setLoading] = useState(false);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Background Services</h1>

      <Card>
        <div className="space-y-2">
          {services.map((service) => (
            <div
              key={service.id}
              className="flex items-center justify-between p-3 bg-background rounded border border-border"
            >
              <div>
                <p className="font-medium">{service.name}</p>
                <p className="text-sm text-gray-400">Uptime: {service.uptime}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    service.status === "running" ? "secondary" : "danger"
                  }
                >
                  {service.status}
                </Badge>
                <Button size="sm" variant="ghost">
                  Restart
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
