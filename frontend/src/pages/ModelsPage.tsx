import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/appStore";
import {
  getAllModels,
  getProviders,
  validateProvider,
  createProvider,
  updateProvider,
  deleteProvider,
  deleteModel,
  startModelDownload,
  listModelDownloads,
  cancelModelDownload,
  resumeModelDownload,
  getRoutingProfiles,
  selectRoutingProfile,
  getRoutingRoutes,
  updateRoutingRoutes,
  getProviderModels,
  setProviderDefaultModel as updateProviderDefaultModel,
  type RegisteredModel,
  type Provider,
  type RoutingProfile,
  type TaskRoute,
  type ProviderModelsResponse,
} from "@/api/ai";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  AlertTriangle,
  ArrowRightLeft,
  Check,
  CheckCircle2,
  ChevronDown,
  Cpu,
  Download,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  Trash2,
  Wand2,
} from "lucide-react";

type TabKey = "providers" | "routing" | "status";

const TASKS = [
  { task_type: "chat", label: "Chat", helper: "General conversation and lightweight assist." },
  { task_type: "coding", label: "Coding", helper: "Code generation, refactors, and patching." },
  { task_type: "search", label: "Search", helper: "Finding files, docs, and references." },
  { task_type: "repository_analysis", label: "Repo Analysis", helper: "Cross-file understanding and architecture." },
  { task_type: "planning", label: "Planning", helper: "Roadmaps, breakdowns, and next steps." },
  { task_type: "memory", label: "Memory", helper: "Session memory and recall-heavy work." },
  { task_type: "debugging", label: "Debugging", helper: "Error analysis and root-cause fixing." },
] as const;

function formatLabel(value?: string | null) {
  if (!value) return "N/A";
  return value
    .replace(/[:_]/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function modelDisplayName(model: RegisteredModel) {
  return model.display_name || model.name;
}

function modelOptionLabel(name: string) {
  return formatLabel(name);
}

export function ModelsPage() {
  const qc = useQueryClient();
  const setToast = useAppStore((s) => s.setToast);

  const [activeTab, setActiveTab] = useState<TabKey>("providers");
  const [searchQuery, setSearchQuery] = useState("");

  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [providerName, setProviderName] = useState("");
  const [providerUrl, setProviderUrl] = useState("");
  const [providerKey, setProviderKey] = useState("");
  const [providerDefaultModel, setProviderDefaultModelName] = useState("");
  const [isCustom, setIsCustom] = useState(false);
  const [validationResult, setValidationResult] = useState<ProviderModelsResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const [pullModelName, setPullModelName] = useState("");
  const { data: downloadJobs = [] } = useQuery({
    queryKey: ["modelDownloads"],
    queryFn: listModelDownloads,
    refetchInterval: 2000,
  });

  const { data: models = [], isLoading: loadingModels, refetch: refetchModels } = useQuery<RegisteredModel[]>({
    queryKey: ["models"],
    queryFn: getAllModels,
  });

  const { data: providers = [], isLoading: loadingProviders, refetch: refetchProviders } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: getProviders,
  });

  const { data: routingProfiles = [] } = useQuery<RoutingProfile[]>({
    queryKey: ["routingProfiles"],
    queryFn: getRoutingProfiles,
  });

  const { data: routingRoutesResponse, isLoading: loadingRoutes } = useQuery({
    queryKey: ["routingRoutes"],
    queryFn: getRoutingRoutes,
  });

  const activeProfileName = routingRoutesResponse?.profile_name || "Balanced";
  const activeRoutes = routingRoutesResponse?.routes || [];
  const customProfileActive = activeProfileName.toLowerCase() === "custom";
  const [routeDrafts, setRouteDrafts] = useState<TaskRoute[]>(() =>
    TASKS.map((task) => ({
      task_type: task.task_type,
      primary_model: "Auto",
      fallback_model: "Auto",
    })),
  );

  const providerModelsQuery = useQuery<ProviderModelsResponse>({
    queryKey: ["providerModels", selectedProvider?.name],
    queryFn: () => getProviderModels(selectedProvider?.name || ""),
    enabled: Boolean(selectedProvider?.id && selectedProvider?.name),
  });

  const providerModelChoices = useMemo(() => {
    const remoteModels = providerModelsQuery.data?.models ?? validationResult?.models ?? [];
    const merged = new Set<string>();
    const normalized: string[] = [];
    for (const item of remoteModels) {
      if (item && !merged.has(item)) {
        merged.add(item);
        normalized.push(item);
      }
    }
    return normalized;
  }, [providerModelsQuery.data?.models, validationResult?.models]);

  const allModelNames = useMemo(() => {
    const names = new Set<string>();
    const ordered: string[] = [];
    for (const model of models) {
      const name = model.name;
      if (!names.has(name)) {
        names.add(name);
        ordered.push(name);
      }
    }
    return ordered;
  }, [models]);

  const localModels = models.filter((m) => m.is_local);
  const cloudModels = models.filter((m) => !m.is_local);

  const visibleLocalModels = localModels.filter((model) => {
    const haystack = [model.name, model.provider, model.parameters, model.quantization, model.vram_estimate]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(searchQuery.toLowerCase());
  });

  const selectProviderForEdit = (provider: Provider) => {
    setSelectedProvider(provider);
    setProviderName(provider.name);
    setProviderUrl(provider.base_url || "");
    setProviderKey(provider.has_key ? "••••••••••••••••" : "");
    setProviderDefaultModelName(provider.default_model_name || "");
    setIsCustom(provider.is_custom);
    setValidationResult(null);
  };

  const startNewProvider = () => {
    const blank = {
      name: "",
      base_url: "",
      is_enabled: false,
      is_custom: true,
      has_key: false,
      default_model_name: null,
    } as Provider;
    setSelectedProvider(blank);
    setProviderName("");
    setProviderUrl("");
    setProviderKey("");
    setProviderDefaultModelName("");
    setIsCustom(true);
    setValidationResult(null);
  };

  const providerFormReady = providerName.trim().length > 0;

  const runValidation = async () => {
    if (!providerName || !providerUrl || !providerKey || providerKey === "••••••••••••••••") {
      setToast("Name, URL, and API key are required for validation.");
      return;
    }

    setIsValidating(true);
    setValidationResult(null);
    try {
      const res = await validateProvider(providerName, providerUrl, providerKey);
      setValidationResult(res);
      if (res.valid) {
        setToast(`Connection validated. ${res.models.length} models discovered.`);
        if (!providerDefaultModel && res.default_model) {
          setProviderDefaultModelName(res.default_model);
        }
      } else {
        setToast(`Validation failed: ${res.error || "unknown error"}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown validation error";
      setValidationResult({ valid: false, models: [], error: message, provider_name: providerName, default_model_name: null });
      setToast(`Validation failed: ${message}`);
    } finally {
      setIsValidating(false);
    }
  };

  const saveProvider = async (enabledStatus?: boolean) => {
    if (!providerFormReady) {
      setToast("Provider name is required.");
      return;
    }

    const payload = {
      name: providerName.trim(),
      base_url: providerUrl.trim() || undefined,
      api_key: providerKey === "••••••••••••••••" ? undefined : providerKey,
      default_model_name: providerDefaultModel || undefined,
      is_enabled: enabledStatus ?? (selectedProvider?.is_enabled ?? true),
      is_custom: isCustom,
    };

    try {
      if (selectedProvider?.id !== undefined) {
        await updateProvider(selectedProvider.name, payload);
        setToast("Provider updated.");
      } else {
        await createProvider(payload);
        setToast("Provider created.");
      }

      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["models"] });
      setSelectedProvider(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to save provider";
      setToast(message);
    }
  };

  const saveDefaultModel = async () => {
    if (!selectedProvider?.name || !providerDefaultModel) {
      setToast("Pick a default model first.");
      return;
    }

    try {
      await updateProviderDefaultModel(selectedProvider.name, providerDefaultModel);
      qc.invalidateQueries({ queryKey: ["providers"] });
      setToast("Provider default model updated.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to update default model";
      setToast(message);
    }
  };

  const deleteProviderMutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: () => {
      setToast("Provider deleted.");
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["models"] });
      setSelectedProvider(null);
    },
    onError: (err: Error) => {
      setToast(`Failed to delete provider: ${err.message}`);
    },
  });

  const deleteModelMutation = useMutation({
    mutationFn: deleteModel,
    onSuccess: () => {
      setToast("Local model removed.");
      qc.invalidateQueries({ queryKey: ["models"] });
      qc.invalidateQueries({ queryKey: ["marketplace"] });
    },
    onError: (err: Error) => {
      setToast(`Failed to delete model: ${err.message}`);
    },
  });

  const selectProfileMutation = useMutation({
    mutationFn: selectRoutingProfile,
    onSuccess: () => {
      setToast("Routing profile switched.");
      qc.invalidateQueries({ queryKey: ["routingProfiles"] });
      qc.invalidateQueries({ queryKey: ["routingRoutes"] });
    },
    onError: (err: Error) => setToast(`Failed to switch routing profile: ${err.message}`),
  });

  const updateRoutesMutation = useMutation({
    mutationFn: updateRoutingRoutes,
    onSuccess: () => {
      setToast("Task routing saved.");
      qc.invalidateQueries({ queryKey: ["routingRoutes"] });
      qc.invalidateQueries({ queryKey: ["models"] });
    },
    onError: (err: Error) => setToast(`Failed to save routing rules: ${err.message}`),
  });

  const handlePull = async () => {
    if (!pullModelName.trim()) return;

    try {
      const job = await startModelDownload(pullModelName.trim());
      setToast(`Download ${job.status}: ${job.model}`);
      setPullModelName("");
      qc.invalidateQueries({ queryKey: ["models"] });
      qc.invalidateQueries({ queryKey: ["marketplace"] });
      qc.invalidateQueries({ queryKey: ["modelDownloads"] });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed";
      setToast(message);
    }
  };

  const cancelPull = async () => {
    if (!activeDownload) return;
    await cancelModelDownload(activeDownload.id);
    qc.invalidateQueries({ queryKey: ["modelDownloads"] });
    setToast("Download cancelled.");
  };

  const resumePull = async () => {
    if (!activeDownload) return;
    await resumeModelDownload(activeDownload.id);
    qc.invalidateQueries({ queryKey: ["modelDownloads"] });
    setToast("Download resumed.");
  };

  const updateRoute = (taskType: string, field: "primary_model" | "fallback_model", value: string) => {
    const nextRoutes: TaskRoute[] = routeDrafts.map((route) =>
      route.task_type === taskType ? { ...route, [field]: value } : route,
    );
    setRouteDrafts(nextRoutes);
  };

  const summaryCards = [
    { label: "Active Profile", value: activeProfileName, icon: Shield },
    { label: "Local Models", value: String(localModels.length), icon: Cpu },
    { label: "Cloud Models", value: String(cloudModels.length), icon: Wand2 },
    { label: "Providers", value: String(providers.length), icon: Activity },
  ];

  const providerModelHint = providerModelChoices.length > 0 ? providerModelChoices : allModelNames;
  const activeDownload = downloadJobs.find(
    (job) => job.model === pullModelName.trim() && !["completed", "failed", "cancelled"].includes(job.status),
  ) || downloadJobs.find((job) => !["completed", "failed", "cancelled"].includes(job.status));

  useEffect(() => {
    const draftRoutes = TASKS.map((task) => {
      const existing = activeRoutes.find((route) => route.task_type === task.task_type);
      return existing || {
        task_type: task.task_type,
        primary_model: allModelNames[0] || "Auto",
        fallback_model: allModelNames[1] || allModelNames[0] || "Auto",
      };
    });
    setRouteDrafts(draftRoutes);
  }, [activeRoutes, activeProfileName, allModelNames]);

  return (
    <div className="h-full overflow-y-auto bg-cortex-bg px-4 py-6 md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-3xl border border-cortex-border bg-gradient-to-br from-cortex-surface/80 via-cortex-surface/40 to-cortex-elevated/20 p-6 shadow-2xl shadow-black/20">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-cortex-accent/20 bg-cortex-accent-soft/50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cortex-accent">
                <Sparkles className="h-3.5 w-3.5" />
                Cortex model operations
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight text-cortex-text md:text-4xl">
                  Models, marketplace, and routing
                </h1>
                <p className="mt-2 max-w-3xl text-sm text-cortex-muted">
                  Manage providers, verify keys, pull local models, and control task-based routing without leaving this dashboard.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" size="sm" onClick={() => { refetchModels(); refetchProviders(); qc.invalidateQueries({ queryKey: ["routingRoutes"] }); }} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button variant="secondary" size="sm" onClick={() => { setActiveTab("providers"); startNewProvider(); }} className="gap-2">
                <Plus className="h-4 w-4" />
                Add Provider
              </Button>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {summaryCards.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.label} className="rounded-2xl border border-cortex-border bg-cortex-elevated/60 p-4 transition hover:border-cortex-accent/40 hover:bg-cortex-elevated/80">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">
                    <Icon className="h-4 w-4 text-cortex-accent" />
                    {card.label}
                  </div>
                  <div className="mt-2 text-2xl font-black text-cortex-text">{card.value}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 border-b border-cortex-border pb-2">
          {[
            { key: "providers", label: "Provider Console" },
            { key: "routing", label: "Task Routing" },
            { key: "status", label: "System Status" },
          ].map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key as TabKey)}
              className={cn(
                "rounded-full border px-4 py-2 text-sm font-semibold transition",
                activeTab === tab.key
                  ? "border-cortex-accent bg-cortex-accent-soft text-cortex-accent shadow-lg shadow-cortex-accent/10"
                  : "border-cortex-border bg-cortex-surface/40 text-cortex-muted hover:border-cortex-border-hover hover:text-cortex-text",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "providers" && (
          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.55fr]">
            <Card className="border-cortex-border bg-cortex-surface/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-base">Providers</CardTitle>
                <CardDescription>OpenAI-compatible APIs, Anthropic, Gemini, Groq, Together AI, and custom endpoints.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {loadingProviders ? (
                  <div className="flex items-center justify-center py-10">
                    <Loader2 className="h-5 w-5 animate-spin text-cortex-accent" />
                  </div>
                ) : providers.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-cortex-border p-6 text-center text-sm text-cortex-muted">
                    No providers configured yet.
                  </div>
                ) : (
                  providers.map((provider) => (
                    <button
                      key={provider.name}
                      type="button"
                      onClick={() => selectProviderForEdit(provider)}
                      className={cn(
                        "flex w-full items-center justify-between rounded-2xl border p-4 text-left transition",
                        selectedProvider?.name === provider.name
                          ? "border-cortex-accent bg-cortex-accent-soft/20 shadow-lg shadow-cortex-accent/10"
                          : "border-cortex-border bg-cortex-elevated/40 hover:border-cortex-border-hover hover:bg-cortex-elevated/70",
                      )}
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="truncate font-semibold text-cortex-text">{provider.name}</span>
                          {provider.default_model_name && (
                            <Badge variant="accent" className="text-[10px]">
                              Default: {formatLabel(provider.default_model_name)}
                            </Badge>
                          )}
                        </div>
                        <p className="mt-1 truncate text-xs text-cortex-muted">{provider.base_url || "Custom endpoint"}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {provider.is_enabled ? <Badge variant="accent">Enabled</Badge> : <Badge variant="default">Disabled</Badge>}
                        <ChevronDown className="h-4 w-4 text-cortex-muted" />
                      </div>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="border-cortex-border bg-cortex-surface/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-base">
                  {selectedProvider?.id !== undefined ? "Edit Provider" : "Create Provider"}
                </CardTitle>
                <CardDescription>
                  Validate the connection, inspect live models, and choose the provider default model.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedProvider ? (
                  <>
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Provider name</label>
                        <Input value={providerName} onChange={(e) => setProviderName(e.target.value)} disabled={!isCustom && selectedProvider.id !== undefined} placeholder="OpenAI, Anthropic, Google Gemini..." />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Base URL</label>
                        <Input value={providerUrl} onChange={(e) => setProviderUrl(e.target.value)} placeholder="https://api.openai.com/v1" />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">API key</label>
                      <Input
                        type="password"
                        value={providerKey}
                        onChange={(e) => setProviderKey(e.target.value)}
                        placeholder="Paste secret key"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Default model</label>
                      <select
                        value={providerDefaultModel}
                        onChange={(e) => setProviderDefaultModelName(e.target.value)}
                        className="h-10 w-full rounded-xl border border-cortex-border bg-cortex-surface px-3 text-sm text-cortex-text outline-none transition focus:border-cortex-accent"
                      >
                        <option value="">Choose a default model</option>
                        {providerModelHint.map((modelName) => (
                          <option key={modelName} value={modelName}>
                            {modelOptionLabel(modelName)}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={runValidation} disabled={isValidating || !providerName || !providerUrl || !providerKey || providerKey === "••••••••••••••••"} className="gap-2">
                        {isValidating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
                        Test connection
                      </Button>
                      <Button onClick={() => saveProvider()} disabled={!providerName.trim()} className="gap-2">
                        Save provider
                      </Button>
                      {selectedProvider.id !== undefined && (
                        <>
                          <Button variant="secondary" onClick={saveDefaultModel} disabled={!providerDefaultModel}>
                            Save default model
                          </Button>
                          <Button
                            variant={selectedProvider.is_enabled ? "secondary" : "default"}
                            onClick={() => saveProvider(!selectedProvider.is_enabled)}
                          >
                            {selectedProvider.is_enabled ? "Disable" : "Enable"}
                          </Button>
                          {selectedProvider.is_custom && (
                            <Button
                              variant="ghost"
                              className="text-red-400 hover:bg-red-500/10 hover:text-red-300"
                              onClick={() => deleteProviderMutation.mutate(selectedProvider.name)}
                            >
                              Delete
                            </Button>
                          )}
                        </>
                      )}
                    </div>

                    {validationResult && (
                      <div className={cn(
                        "rounded-2xl border p-4 text-sm",
                        validationResult.valid
                          ? "border-green-500/30 bg-green-500/10 text-green-300"
                          : "border-red-500/30 bg-red-500/10 text-red-300",
                      )}>
                        <div className="flex items-center gap-2 font-semibold">
                          {validationResult.valid ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                          {validationResult.valid ? "Connection healthy" : "Connection failed"}
                        </div>
                        <p className="mt-2 text-cortex-muted">
                          {validationResult.valid
                            ? `Discovered ${validationResult.models.length} models.`
                            : validationResult.error || "The provider did not return a usable response."}
                        </p>
                      </div>
                    )}

                    <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Live model discovery</p>
                          <p className="mt-1 text-sm text-cortex-text">Models available from this provider</p>
                        </div>
                        <Badge variant="accent">{providerModelHint.length}</Badge>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {providerModelHint.slice(0, 12).map((name) => (
                          <Badge key={name} variant="default" className="bg-cortex-surface text-cortex-text">
                            {formatLabel(name)}
                          </Badge>
                        ))}
                        {providerModelHint.length === 0 && (
                          <span className="text-sm text-cortex-muted">Run validation to discover models.</span>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="flex min-h-[340px] items-center justify-center rounded-3xl border border-dashed border-cortex-border bg-cortex-elevated/20 p-6 text-center text-sm text-cortex-muted">
                    Select a provider to edit or create a new one.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "routing" && (
          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.55fr]">
            <Card className="border-cortex-border bg-cortex-surface/50">
              <CardHeader>
                <CardTitle className="text-base">Routing profile</CardTitle>
                <CardDescription>Switch between auto routing and custom task overrides.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {routingProfiles.map((profile) => {
                  const active = profile.name.toLowerCase() === activeProfileName.toLowerCase();
                  return (
                    <button
                      key={profile.name}
                      type="button"
                      onClick={() => selectProfileMutation.mutate(profile.name)}
                      className={cn(
                        "flex w-full items-center justify-between rounded-2xl border p-4 text-left transition",
                        active
                          ? "border-cortex-accent bg-cortex-accent-soft/20 shadow-lg shadow-cortex-accent/10"
                          : "border-cortex-border bg-cortex-elevated/40 hover:border-cortex-border-hover hover:bg-cortex-elevated/70",
                      )}
                    >
                      <div>
                        <p className="font-semibold text-cortex-text">{profile.name}</p>
                        <p className="mt-1 text-xs text-cortex-muted">
                          {profile.name === "Balanced"
                            ? "Balanced latency and quality."
                            : profile.name === "Coding Heavy"
                              ? "Biases toward coding-capable models."
                              : profile.name === "Local Only"
                                ? "Uses local models first."
                                : profile.name === "Maximum Quality"
                                  ? "Highest quality cloud-first routing."
                                  : "Fully manual task overrides."}
                        </p>
                      </div>
                      {active && <Check className="h-4 w-4 text-cortex-accent" />}
                    </button>
                  );
                })}

                <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Auto routing</p>
                      <p className="mt-1 text-sm text-cortex-text">When enabled, Cortex picks the best available model.</p>
                    </div>
                    <Badge variant={customProfileActive ? "default" : "accent"}>{customProfileActive ? "Manual" : "Auto"}</Badge>
                  </div>
                  <div className="mt-3 text-xs text-cortex-muted">
                    Manual route editing is available when the Custom profile is active.
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-cortex-border bg-cortex-surface/50">
              <CardHeader>
                <CardTitle className="text-base">Task to model mapping</CardTitle>
                <CardDescription>Choose a primary and fallback model for each workspace task.</CardDescription>
              </CardHeader>
              <CardContent>
                {loadingRoutes ? (
                  <div className="flex items-center justify-center py-10">
                    <Loader2 className="h-5 w-5 animate-spin text-cortex-accent" />
                  </div>
                ) : (
                  <div className="space-y-4">
                        {routeDrafts.map((route) => {
                      const taskMeta = TASKS.find((task) => task.task_type === route.task_type)!;
                      return (
                        <div key={route.task_type} className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4 transition hover:border-cortex-border-hover">
                          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <p className="font-semibold text-cortex-text">{taskMeta.label}</p>
                                <Badge variant="default" className="bg-cortex-accent-soft text-cortex-accent">
                                  {taskMeta.task_type}
                                </Badge>
                              </div>
                              <p className="text-xs text-cortex-muted">{taskMeta.helper}</p>
                            </div>
                            <Badge variant="accent">
                              {activeProfileName}
                            </Badge>
                          </div>

                          <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto_1fr] md:items-center">
                            <select
                              value={route.primary_model}
                              onChange={(e) => updateRoute(route.task_type, "primary_model", e.target.value)}
                              className="h-10 w-full rounded-xl border border-cortex-border bg-cortex-surface px-3 text-sm text-cortex-text outline-none transition focus:border-cortex-accent"
                            >
                              {allModelNames.map((name) => (
                                <option key={name} value={name}>{modelOptionLabel(name)}</option>
                              ))}
                            </select>
                            <div className="flex items-center justify-center text-cortex-muted">
                              <ArrowRightLeft className="h-4 w-4" />
                            </div>
                            <select
                              value={route.fallback_model}
                              onChange={(e) => updateRoute(route.task_type, "fallback_model", e.target.value)}
                              className="h-10 w-full rounded-xl border border-cortex-border bg-cortex-surface px-3 text-sm text-cortex-text outline-none transition focus:border-cortex-accent"
                            >
                              {allModelNames.map((name) => (
                                <option key={name} value={name}>{modelOptionLabel(name)}</option>
                              ))}
                            </select>
                          </div>

                          <div className="mt-3 flex items-center justify-between text-xs text-cortex-muted">
                            <span>Primary model</span>
                            <span>Fallback model</span>
                          </div>
                        </div>
                      );
                    })}

                    <div className="flex flex-wrap gap-2 pt-2">
                      <Button
                        variant="secondary"
                        onClick={() => updateRoutesMutation.mutate(routeDrafts)}
                        className="gap-2"
                      >
                        <Check className="h-4 w-4" />
                        Save routing
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => selectProfileMutation.mutate("Custom")}
                        className="gap-2"
                      >
                        <Wand2 className="h-4 w-4" />
                        Switch to custom
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "status" && (
          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <Card className="border-cortex-border bg-cortex-surface/50">
              <CardHeader>
                <CardTitle className="text-base">Local model inventory</CardTitle>
                <CardDescription>Installed local models with quick actions and status cues.</CardDescription>
                <div className="relative mt-3">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search model name, provider, or quantization..."
                    className="pl-9"
                  />
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-cortex-muted" />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {loadingModels ? (
                  <div className="grid gap-3 md:grid-cols-2">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <div key={index} className="h-32 animate-pulse rounded-2xl border border-cortex-border bg-cortex-elevated/40" />
                    ))}
                  </div>
                ) : visibleLocalModels.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-cortex-border p-8 text-center text-sm text-cortex-muted">
                    No local models match the current search.
                  </div>
                ) : (
                  <div className="grid gap-3 md:grid-cols-2">
                    {visibleLocalModels.map((model) => (
                      <div
                        key={model.name}
                        className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4 transition hover:border-cortex-border-hover hover:bg-cortex-elevated/70"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate font-semibold text-cortex-text">{modelDisplayName(model)}</p>
                            <p className="mt-1 text-xs text-cortex-muted">{model.provider}</p>
                          </div>
                          <Badge variant="accent">{model.status}</Badge>
                        </div>

                        <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-cortex-muted">
                          <div>
                            <p className="uppercase tracking-wider">Context</p>
                            <p className="mt-1 font-semibold text-cortex-text">{model.context_length?.toLocaleString() || "N/A"}</p>
                          </div>
                          <div>
                            <p className="uppercase tracking-wider">Parameters</p>
                            <p className="mt-1 font-semibold text-cortex-text">{model.parameters || "N/A"}</p>
                          </div>
                          <div>
                            <p className="uppercase tracking-wider">Quantization</p>
                            <p className="mt-1 font-semibold text-cortex-text">{model.quantization || "N/A"}</p>
                          </div>
                          <div>
                            <p className="uppercase tracking-wider">VRAM</p>
                            <p className="mt-1 font-semibold text-cortex-accent">{model.vram_estimate || "N/A"}</p>
                          </div>
                        </div>

                        <div className="mt-4 flex items-center justify-between gap-2">
                          <Badge variant="default" className="bg-cortex-accent-soft text-cortex-accent">
                            {model.default_for_provider ? "Provider default" : "Local"}
                          </Badge>
                          <div className="flex gap-2">
                            {model.provider === "Ollama" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-400 hover:bg-red-500/10 hover:text-red-300"
                                onClick={() => deleteModelMutation.mutate(model.name)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="border-cortex-border bg-cortex-surface/50">
                <CardHeader>
                  <CardTitle className="text-base">Local download</CardTitle>
                  <CardDescription>Pull a model from the Ollama registry with live progress and cancellation.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      value={pullModelName}
                      onChange={(e) => setPullModelName(e.target.value)}
                      placeholder="qwen2.5-coder:7b, llama3.1, mistral..."
                    />
                    <Button onClick={handlePull} disabled={!pullModelName.trim()} className="gap-2">
                      <Download className="h-4 w-4" />
                      Pull
                    </Button>
                  </div>
                  {activeDownload && (
                    <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                      <div className="flex items-center justify-between text-xs font-semibold text-cortex-text">
                        <span>{activeDownload.model}</span>
                        <span>{activeDownload.percent}%</span>
                      </div>
                      <div className="mt-3 h-2 overflow-hidden rounded-full bg-cortex-border">
                        <div className="h-full rounded-full bg-cortex-accent transition-all duration-300" style={{ width: `${activeDownload.percent}%` }} />
                      </div>
                      <p className="mt-2 text-[11px] text-cortex-muted">
                        {activeDownload.completed !== undefined && activeDownload.total ? (
                          <>
                            {(activeDownload.completed / 1024 / 1024 / 1024).toFixed(2)} GB / {(activeDownload.total / 1024 / 1024 / 1024).toFixed(2)} GB
                          </>
                        ) : (
                          activeDownload.message || "Waiting for download telemetry..."
                        )}
                      </p>
                      <div className="mt-3 flex gap-2">
                        <Button variant="secondary" onClick={cancelPull}>
                          Cancel download
                        </Button>
                        {(activeDownload.status === "cancelled" || activeDownload.status === "failed") && (
                          <Button variant="secondary" onClick={resumePull}>
                            Resume download
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-cortex-border bg-cortex-surface/50">
                <CardHeader>
                  <CardTitle className="text-base">Routing overview</CardTitle>
                  <CardDescription>Current profile and fallback behavior at a glance.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                    <p className="text-xs uppercase tracking-wider text-cortex-muted">Active profile</p>
                    <p className="mt-1 text-lg font-black text-cortex-text">{activeProfileName}</p>
                  </div>
                  <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4">
                    <p className="text-xs uppercase tracking-wider text-cortex-muted">Fallback rule</p>
                    <p className="mt-1 text-sm text-cortex-text">If primary routing fails, Cortex falls back to the configured secondary model, then the local default.</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
