"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button } from "@/components/ui/base";
import { modelsService } from "@/services/api/models";
import type { CortexModel } from "@/types/api";

export default function AdminModelsPage() {
  const [models, setModels] = useState<CortexModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const data = await modelsService.listAllModels();
        setModels(data);
      } catch (error) {
        console.error("Failed to fetch models:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
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
      <h1 className="text-3xl font-bold">Model Registry</h1>

      <Card>
        <h2 className="text-xl font-bold mb-4">Available Models</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-border">
              <tr>
                <th className="pb-2 text-gray-400">Name</th>
                <th className="pb-2 text-gray-400">Type</th>
                <th className="pb-2 text-gray-400">Provider</th>
                <th className="pb-2 text-gray-400">Context</th>
                <th className="pb-2 text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody className="space-y-2">
              {models.map((model) => (
                <tr key={model.id} className="border-b border-border hover:bg-surface">
                  <td className="py-2 font-medium">{model.name}</td>
                  <td className="py-2">
                    <Badge>{model.type}</Badge>
                  </td>
                  <td className="py-2 text-sm text-gray-400">
                    {model.provider_id || "N/A"}
                  </td>
                  <td className="py-2 text-sm text-gray-400">
                    {model.context_length || "-"}
                  </td>
                  <td className="py-2">
                    <Button size="sm" variant="ghost">
                      View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
