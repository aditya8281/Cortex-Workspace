import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/stores/appStore";
import { cn } from "@/lib/utils";
import { 
  getAllModels, 
  getProviders, 
  validateProvider, 
  createProvider, 
  updateProvider, 
  deleteProvider, 
  pullModel,
  deleteModel,
  type RegisteredModel,
  type Provider
} from "@/api/ai";
import { Trash2, Shield, Play, Loader2, RefreshCw, Plus, CheckCircle, AlertTriangle } from "lucide-react";

export function ModelsPage() {
  const qc = useQueryClient();
  const setToast = useAppStore((s) => s.setToast);

  // Queries
  const { data: models = [], isLoading: loadingModels, refetch: refetchModels } = useQuery<RegisteredModel[]>({
    queryKey: ["models"],
    queryFn: getAllModels,
  });

  const { data: providers = [], isLoading: loadingProviders, refetch: refetchProviders } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: getProviders,
  });

  // Pull Model State
  const [pullModelName, setPullModelName] = useState("");
  const [pullProgress, setPullProgress] = useState<{ status: string; percent: number; completed?: number; total?: number } | null>(null);
  const [isPulling, setIsPulling] = useState(false);

  // Provider Form State
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [providerKey, setProviderKey] = useState("");
  const [providerUrl, setProviderUrl] = useState("");
  const [providerName, setProviderName] = useState("");
  const [isCustom, setIsCustom] = useState(false);

  const [validationResult, setValidationResult] = useState<{ valid: boolean; models?: string[]; test_response?: string; error?: string } | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Mutations
  const deleteModelMutation = useMutation({
    mutationFn: deleteModel,
    onSuccess: () => {
      setToast("Local model deleted successfully");
      qc.invalidateQueries({ queryKey: ["models"] });
    },
    onError: (err: Error) => {
      setToast(`Failed to delete model: ${err.message || err}`);
    }
  });

  const deleteProviderMutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: () => {
      setToast("Provider deleted");
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["models"] });
      setSelectedProvider(null);
    }
  });

  // Select provider to edit
  const selectProviderForEdit = (p: Provider) => {
    setSelectedProvider(p);
    setProviderName(p.name);
    setProviderUrl(p.base_url || "");
    setProviderKey(p.has_key ? "••••••••••••••••" : "");
    setIsCustom(p.is_custom);
    setValidationResult(null);
  };

  const startNewProvider = () => {
    setSelectedProvider({
      name: "",
      base_url: "",
      is_enabled: false,
      is_custom: true,
      has_key: false
    });
    setProviderName("");
    setProviderUrl("");
    setProviderKey("");
    setIsCustom(true);
    setValidationResult(null);
  };

  // Run validation
  const runValidation = async () => {
    if (!providerName || !providerUrl || !providerKey) {
      setToast("Name, URL, and Key are required for validation");
      return;
    }
    setIsValidating(true);
    setValidationResult(null);
    try {
      const res = await validateProvider(providerName, providerUrl, providerKey);
      setValidationResult(res);
      if (res.valid) {
        setToast("Connection validated successfully!");
      } else {
        setToast("Connection validation failed.");
      }
    } catch (e: unknown) {
      const err = e as Error;
      setValidationResult({ valid: false, error: err.message || "Failed to call validation API" });
      setToast("Validation failed");
    } finally {
      setIsValidating(false);
    }
  };

  // Save provider
  const saveProvider = async (enabledStatus?: boolean) => {
    if (!providerName) {
      setToast("Provider Name is required");
      return;
    }

    const payload = {
      name: providerName,
      base_url: providerUrl,
      api_key: providerKey === "••••••••••••••••" ? undefined : providerKey,
      is_enabled: enabledStatus !== undefined ? enabledStatus : (selectedProvider?.is_enabled ?? true),
      is_custom: isCustom
    };

    try {
      if (selectedProvider?.id !== undefined) {
        await updateProvider(selectedProvider.name, payload);
        setToast("Provider updated successfully");
      } else {
        await createProvider(payload);
        setToast("Provider created successfully");
      }
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["models"] });
      setSelectedProvider(null);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      setToast(`Error saving provider: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handle model pull
  const executePull = async () => {
    if (!pullModelName.trim()) return;
    setIsPulling(true);
    setPullProgress({ status: "Starting pull...", percent: 0 });
    try {
      await pullModel(pullModelName.trim(), (progress) => {
        setPullProgress(progress);
      });
      setToast(`Downloaded model ${pullModelName}`);
      setPullModelName("");
      setPullProgress(null);
      qc.invalidateQueries({ queryKey: ["models"] });
    } catch (e: unknown) {
      const err = e as Error;
      setToast(`Download failed: ${err.message}`);
    } finally {
      setIsPulling(false);
    }
  };

  // Filter models
  const localModels = models.filter((m) => m.is_local);

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8 bg-cortex-background">
      <div className="mx-auto max-w-5xl space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-cortex-text">Model Management</h2>
            <p className="text-sm text-cortex-muted">Configure and switch between local and cloud providers.</p>
          </div>
          <Button variant="secondary" size="sm" onClick={() => { refetchModels(); refetchProviders(); }} className="gap-2">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </div>

        {/* Installed Local Models */}
        <Card className="border-cortex-border bg-cortex-surface/40">
          <CardHeader>
            <CardTitle className="text-lg">Installed Local Models</CardTitle>
            <CardDescription>Detected local model servers (Ollama / LM Studio).</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingModels ? (
              <div className="flex justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-cortex-accent" />
              </div>
            ) : localModels.length === 0 ? (
              <div className="rounded-lg border border-dashed border-cortex-border p-8 text-center text-sm text-cortex-muted italic">
                No local models running. Start Ollama (11434) or LM Studio (1234) to automatically scan.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-cortex-border text-cortex-muted uppercase tracking-wider font-semibold">
                      <th className="py-2.5 px-3">Name</th>
                      <th className="py-2.5 px-3">Provider</th>
                      <th className="py-2.5 px-3">Context</th>
                      <th className="py-2.5 px-3">Parameters</th>
                      <th className="py-2.5 px-3">Quant</th>
                      <th className="py-2.5 px-3">VRAM Est.</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {localModels.map((m) => (
                      <tr key={m.name} className="border-b border-cortex-border/50 hover:bg-white/5 transition-colors">
                        <td className="py-3 px-3 font-semibold text-cortex-text">{m.name}</td>
                        <td className="py-3 px-3 text-cortex-muted">{m.provider}</td>
                        <td className="py-3 px-3">{m.context_length?.toLocaleString() || "N/A"}</td>
                        <td className="py-3 px-3">{m.parameters || "N/A"}</td>
                        <td className="py-3 px-3">{m.quantization || "N/A"}</td>
                        <td className="py-3 px-3 text-cortex-accent">{m.vram_estimate || "N/A"}</td>
                        <td className="py-3 px-3">
                          <Badge variant="accent">active</Badge>
                        </td>
                        <td className="py-3 px-3 text-right">
                          {m.provider === "Ollama" && (
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              onClick={() => deleteModelMutation.mutate(m.name)} 
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 w-7"
                              title="Delete Model"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cloud Providers and API Keys */}
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-1 border-cortex-border bg-cortex-surface/40">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle className="text-base">Cloud Providers</CardTitle>
                <CardDescription>Configure credentials.</CardDescription>
              </div>
              <Button size="icon" variant="ghost" className="h-8 w-8 text-cortex-accent" onClick={startNewProvider}>
                <Plus className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-cortex-border border-t border-cortex-border">
                {loadingProviders ? (
                  <div className="flex justify-center p-4">
                    <Loader2 className="h-5 w-5 animate-spin text-cortex-accent" />
                  </div>
                ) : (
                  providers.map((p) => (
                    <button
                      key={p.name}
                      onClick={() => selectProviderForEdit(p)}
                      className={cn(
                        "flex w-full items-center justify-between p-3.5 text-left text-xs transition-colors hover:bg-white/5",
                        selectedProvider?.name === p.name && "bg-white/5 border-l-2 border-cortex-accent"
                      )}
                    >
                      <div>
                        <p className="font-semibold text-cortex-text">{p.name}</p>
                        <p className="text-[10px] text-cortex-muted truncate max-w-[200px]">
                          {p.base_url || "Custom Endpoint"}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {p.is_enabled ? (
                          <Badge variant="accent">Enabled</Badge>
                        ) : (
                           <Badge variant="default">Disabled</Badge>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Edit / Configure Provider Form */}
          <Card className="md:col-span-2 border-cortex-border bg-cortex-surface/40">
            <CardHeader>
              <CardTitle className="text-base">
                {selectedProvider 
                  ? `${selectedProvider.id ? "Edit" : "Add"} Provider` 
                  : "Select a Provider"
                }
              </CardTitle>
              <CardDescription>
                {selectedProvider 
                  ? "Enter details to configure credentials and enable models." 
                  : "Choose a provider on the left or add a custom one."
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedProvider ? (
                <div className="space-y-4">
                  <div className="grid gap-2">
                    <label className="text-xs font-semibold text-cortex-muted">Provider Name</label>
                    <Input
                      placeholder="e.g. OpenAI, DeepSeek, MyCustomServer"
                      value={providerName}
                      disabled={!isCustom}
                      onChange={(e) => setProviderName(e.target.value)}
                    />
                  </div>

                  <div className="grid gap-2">
                    <label className="text-xs font-semibold text-cortex-muted">Base URL</label>
                    <Input
                      placeholder="e.g. https://api.openai.com/v1"
                      value={providerUrl}
                      onChange={(e) => setProviderUrl(e.target.value)}
                    />
                  </div>

                  <div className="grid gap-2">
                    <label className="text-xs font-semibold text-cortex-muted">API Key / Token</label>
                    <Input
                      type="password"
                      placeholder="Enter secret key"
                      value={providerKey}
                      onChange={(e) => setProviderKey(e.target.value)}
                    />
                  </div>

                  {/* Validation results */}
                  {validationResult && (
                    <div className={cn(
                      "p-3 rounded-lg border text-xs flex gap-2.5",
                      validationResult.valid 
                        ? "bg-green-500/10 border-green-500/30 text-green-300"
                        : "bg-red-500/10 border-red-500/30 text-red-300"
                    )}>
                      {validationResult.valid ? (
                        <>
                          <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
                          <div>
                            <p className="font-semibold">Connection Validated!</p>
                            <p className="mt-1 text-cortex-muted">
                              Fetched {validationResult.models?.length || 0} models. Sample response: "{validationResult.test_response}"
                            </p>
                          </div>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                          <div>
                            <p className="font-semibold">Validation Failed</p>
                            <p className="mt-1 text-cortex-muted">{validationResult.error}</p>
                          </div>
                        </>
                      )}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={runValidation}
                        disabled={isValidating || !providerKey || !providerUrl}
                        className="gap-2"
                      >
                        {isValidating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Shield className="h-3.5 w-3.5" />}
                        Validate Connection
                      </Button>
                      <Button 
                        size="sm" 
                        onClick={() => saveProvider()} 
                        disabled={selectedProvider.is_enabled && (!validationResult || !validationResult.valid)}
                      >
                        Save
                      </Button>
                    </div>

                    <div className="flex gap-2">
                      {selectedProvider.id !== undefined && (
                        <>
                          <Button
                            variant={selectedProvider.is_enabled ? "secondary" : "default"}
                            size="sm"
                            onClick={() => saveProvider(!selectedProvider.is_enabled)}
                            disabled={!selectedProvider.is_enabled && (!validationResult || !validationResult.valid)}
                          >
                            {selectedProvider.is_enabled ? "Disable" : "Enable"}
                          </Button>

                          {selectedProvider.is_custom && (
                            <Button 
                              variant="ghost" 
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10" 
                              size="sm" 
                              onClick={() => deleteProviderMutation.mutate(selectedProvider.name)}
                            >
                              Delete
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-center text-sm text-cortex-muted italic h-48 border border-dashed border-cortex-border rounded-xl bg-cortex-elevated/20">
                  Select a provider from the list or click '+' to configure credentials.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Model Downloader & Task Routing Placeholder */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Download Local Models */}
          <Card className="border-cortex-border bg-cortex-surface/40">
            <CardHeader>
              <CardTitle className="text-base">Download Local Models</CardTitle>
              <CardDescription>Pull new models from Ollama Library.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. qwen2.5:7b, llama3.1, mistral"
                  value={pullModelName}
                  onChange={(e) => setPullModelName(e.target.value)}
                  disabled={isPulling}
                />
                <Button onClick={executePull} disabled={isPulling || !pullModelName.trim()} className="gap-2">
                  {isPulling ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                  Download
                </Button>
              </div>

              {/* Progress feedback */}
              {pullProgress && (
                <div className="space-y-2 rounded-lg border border-cortex-border bg-cortex-elevated/40 p-3 text-xs">
                  <div className="flex justify-between font-semibold">
                    <span>Status: {pullProgress.status}</span>
                    <span>{pullProgress.percent}%</span>
                  </div>
                  {pullProgress.total && pullProgress.total > 0 && (
                    <div className="w-full bg-cortex-border rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-cortex-accent h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${pullProgress.percent}%` }}
                      />
                    </div>
                  )}
                  <p className="text-[10px] text-cortex-muted">
                    {pullProgress.completed ? `${(pullProgress.completed / 1024 / 1024 / 1024).toFixed(2)} GB` : ""}
                    {pullProgress.total ? ` / ${(pullProgress.total / 1024 / 1024 / 1024).toFixed(2)} GB` : ""}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Task Routing Placeholder */}
          <Card className="border-cortex-border bg-cortex-surface/40 border-dashed">
            <CardHeader>
              <CardTitle className="text-base text-cortex-muted">Task Routing (Future Phase)</CardTitle>
              <CardDescription>Intelligent task and request dispatching.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col justify-center items-center p-6 h-28 text-center text-xs text-cortex-muted">
              <Shield className="h-7 w-7 text-cortex-muted/40 mb-2" />
              <p>Dynamic capabilities routing based on task complexity and VRAM footprint is placeholder scheduled for next phase.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
