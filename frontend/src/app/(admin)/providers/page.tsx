"use client";

import { useState, useEffect } from "react";
import { Button, Card, Input, Spinner, Badge } from "@/components/ui/base";
import { modelsService } from "@/services/api/models";
import type { CortexProvider } from "@/types/api";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<CortexProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    api_base_url: "",
  });

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        setLoading(true);
        const data = await modelsService.listProviders();
        setProviders(data);
      } catch (error) {
        console.error("Failed to fetch providers:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchProviders();
  }, []);

  const handleAddProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const newProvider = await modelsService.addProvider(formData);
      setProviders([...providers, newProvider]);
      setFormData({ name: "", api_base_url: "" });
      setShowForm(false);
    } catch (error) {
      console.error("Failed to add provider:", error);
    }
  };

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
        <h1 className="text-3xl font-bold">Model Providers</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add Provider"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <form onSubmit={handleAddProvider} className="space-y-4">
            <Input
              label="Provider Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            <Input
              label="API Base URL"
              value={formData.api_base_url}
              onChange={(e) =>
                setFormData({ ...formData, api_base_url: e.target.value })
              }
              required
            />
            <Button type="submit">Add Provider</Button>
          </form>
        </Card>
      )}

      <div className="space-y-2">
        {providers.map((provider) => (
          <Card key={provider.id} className="bg-background">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">{provider.name}</h3>
                <p className="text-sm text-gray-400">{provider.api_base_url}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {provider.models?.length || 0} models
                </p>
              </div>
              <Badge
                variant={provider.status === "active" ? "secondary" : "danger"}
              >
                {provider.status}
              </Badge>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
