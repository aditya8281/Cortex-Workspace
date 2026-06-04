"use client";

import { useState, useEffect } from "react";
import { Button, Card, Spinner, Badge } from "@/components/ui/base";
import { modelsService, routingService } from "@/services/api/models";
import type { CortexModel, CortexProvider, CortexRoutingProfile } from "@/types/api";

export default function ModelsPage() {
  const [models, setModels] = useState<CortexModel[]>([]);
  const [providers, setProviders] = useState<CortexProvider[]>([]);
  const [profiles, setProfiles] = useState<CortexRoutingProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [modelsData, providersData, profilesData] = await Promise.all([
          modelsService.listAllModels(),
          modelsService.listProviders(),
          routingService.getProfiles(),
        ]);
        setModels(modelsData);
        setProviders(providersData);
        setProfiles(profilesData);
      } catch (err: any) {
        setError(err.message || "Failed to fetch data");
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
      <h1 className="text-3xl font-bold">Models & Routing</h1>

      {error && <p className="text-danger">{error}</p>}

      {/* Routing Profiles */}
      <Card>
        <h2 className="text-xl font-bold mb-4">Routing Profiles</h2>
        <div className="space-y-2">
          {profiles.map((profile) => (
            <div key={profile.id} className="flex items-center justify-between p-2 bg-background rounded">
              <div>
                <p className="font-medium">{profile.name}</p>
                <p className="text-sm text-gray-400">{profile.description}</p>
              </div>
              {profile.is_active && <Badge>Active</Badge>}
            </div>
          ))}
        </div>
      </Card>

      {/* Providers */}
      <Card>
        <h2 className="text-xl font-bold mb-4">Providers</h2>
        <div className="space-y-2">
          {providers.map((provider) => (
            <div key={provider.id} className="flex items-center justify-between p-2 bg-background rounded">
              <div>
                <p className="font-medium">{provider.name}</p>
                <p className="text-sm text-gray-400">{provider.models?.length || 0} models</p>
              </div>
              <Badge variant={provider.status === "active" ? "secondary" : "danger"}>
                {provider.status}
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      {/* Available Models */}
      <Card>
        <h2 className="text-xl font-bold mb-4">Available Models</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {models.map((model) => (
            <Card key={model.id} className="bg-background">
              <h3 className="font-medium">{model.name}</h3>
              <p className="text-sm text-gray-400">{model.type}</p>
              {model.context_length && (
                <p className="text-xs text-gray-500">Context: {model.context_length}</p>
              )}
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
}
