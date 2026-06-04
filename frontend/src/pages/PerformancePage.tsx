import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/stores/appStore";
import { cn } from "@/lib/utils";
import {
  getMetricsSummary,
  getModelHealth,
  getRoutingAnalytics,
  getRoutingProfiles,
  selectRoutingProfile,
  getAllModels,
  getProviders,
  updateProvider
} from "@/api/ai";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Gauge,
  Cpu,
  Layers,
  Settings,
  Shuffle,
  Shield,
  Zap,
  HardDrive,
  Loader2
} from "lucide-react";

export function PerformancePage() {
  const qc = useQueryClient();
  const setToast = useAppStore((s) => s.setToast);
  const modelConfig = useAppStore((s) => s.modelConfig);
  const setModelConfig = useAppStore((s) => s.setModelConfig);

  const [activeTab, setActiveTab] = useState<"overview" | "health" | "routing" | "settings">("overview");

  // Local state for privacy shield (pure client side)
  const [privacyShield, setPrivacyShield] = useState(() => localStorage.getItem("cortex_privacy_shield") === "true");

  // Query performance summary
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["metricsSummary"],
    queryFn: getMetricsSummary,
    refetchInterval: 5000, // refresh every 5s
  });

  // Query model health
  const { data: health = [], isLoading: loadingHealth } = useQuery({
    queryKey: ["modelHealth"],
    queryFn: getModelHealth,
    refetchInterval: 10000,
  });

  // Query routing analytics
  const { data: analytics, isLoading: loadingAnalytics } = useQuery({
    queryKey: ["routingAnalytics"],
    queryFn: getRoutingAnalytics,
    refetchInterval: 10000,
  });

  // Query routing profiles
  const { data: routingProfiles = [] } = useQuery({
    queryKey: ["routingProfiles"],
    queryFn: getRoutingProfiles,
  });

  // Query registered models for default model selector
  const { data: models = [] } = useQuery({
    queryKey: ["models"],
    queryFn: getAllModels,
  });

  // Query providers list to see which ones are enabled/disabled
  const { data: providers = [] } = useQuery({
    queryKey: ["providers"],
    queryFn: getProviders,
  });

  const selectProfileMutation = useMutation({
    mutationFn: selectRoutingProfile,
    onSuccess: (res: any) => {
      setToast("Routing profile updated");
      qc.invalidateQueries({ queryKey: ["routingProfiles"] });
      qc.invalidateQueries({ queryKey: ["routingRoutes"] });
      qc.invalidateQueries({ queryKey: ["routingAnalytics"] });
    },
    onError: (err: Error) => {
      setToast(`Failed to switch profile: ${err.message}`);
    }
  });

  const updateProviderMutation = useMutation({
    mutationFn: async (args: { name: string; is_enabled: boolean }) => {
      const p = providers.find((prov) => prov.name === args.name);
      if (!p) throw new Error(`Provider ${args.name} not found`);
      return updateProvider(args.name, {
        name: p.name,
        base_url: p.base_url || undefined,
        is_enabled: args.is_enabled,
        is_custom: p.is_custom
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
    }
  });

  // Determine active profile
  const activeProfile = routingProfiles.find((p) => p.is_active)?.name || "Balanced";

  // Derive localOnly status from active routing profile
  const localOnly = activeProfile.toLowerCase() === "local only";

  // Identify local vs cloud providers
  const isLocalProvider = (name: string) =>
    ["ollama", "lm studio", "lm-studio", "system"].includes(name.toLowerCase());
  const cloudProviders = providers.filter((p) => !isLocalProvider(p.name));
  
  // Derive cloudEnabled status: true if any cloud provider is enabled
  const cloudEnabled = cloudProviders.length > 0
    ? cloudProviders.some((p) => p.is_enabled)
    : true;

  const handleToggleLocalOnly = (val: boolean) => {
    selectProfileMutation.mutate(val ? "Local Only" : "Balanced");
    localStorage.setItem("cortex_local_only", String(val));
  };

  const handleToggleCloud = async (val: boolean) => {
    try {
      const cloudProviders = providers.filter((p) => !isLocalProvider(p.name));
      for (const p of cloudProviders) {
        await updateProviderMutation.mutateAsync({ name: p.name, is_enabled: val });
      }
      localStorage.setItem("cortex_cloud_enabled", String(val));
      setToast(val ? "Cloud model providers enabled" : "Cloud model providers disabled");
    } catch (err: any) {
      setToast(`Failed to update providers: ${err.message}`);
    }
  };

  const handleTogglePrivacy = (val: boolean) => {
    setPrivacyShield(val);
    localStorage.setItem("cortex_privacy_shield", String(val));
    setToast(val ? "Privacy Shield enabled: query logs disabled" : "Query logging enabled");
  };


  return (
    <div className="container mx-auto space-y-8 p-6 max-w-7xl">
      {/* Header section with tabs */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-cortex-accent to-cortex-success bg-clip-text text-transparent">
            Performance Dashboard
          </h1>
          <p className="text-cortex-muted text-sm">
            Monitor model response latency, success rate metrics, task routing, and hardware compute metrics.
          </p>
        </div>

        {/* Tab switchers */}
        <div className="flex bg-cortex-elevated/60 p-1 rounded-xl border border-cortex-border shrink-0 self-start md:self-auto">
          {[
            { id: "overview", label: "Overview", icon: Gauge },
            { id: "health", label: "Model Health", icon: Activity },
            { id: "routing", label: "Routing Analytics", icon: Shuffle },
            { id: "settings", label: "Settings", icon: Settings }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition duration-150 cursor-pointer",
                  activeTab === tab.id
                    ? "bg-cortex-accent text-cortex-bg font-bold shadow-md"
                    : "text-cortex-muted hover:text-cortex-text"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-cortex-border bg-cortex-surface/40 hover:bg-cortex-surface/60 transition duration-200">
              <CardHeader className="pb-2">
                <CardDescription className="text-xs uppercase tracking-wider text-cortex-muted font-bold flex items-center justify-between">
                  Avg Latency
                  <Clock className="h-4 w-4 text-cortex-accent" />
                </CardDescription>
                <CardTitle className="text-2xl font-bold mt-1 text-cortex-text">
                  {summary ? `${summary.avg_response_time_ms.toFixed(0)} ms` : "0 ms"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-[10px] text-cortex-success flex items-center gap-0.5">
                  <CheckCircle2 className="h-3 w-3" />
                  Optimized via Router
                </span>
              </CardContent>
            </Card>

            <Card className="border-cortex-border bg-cortex-surface/40 hover:bg-cortex-surface/60 transition duration-200">
              <CardHeader className="pb-2">
                <CardDescription className="text-xs uppercase tracking-wider text-cortex-muted font-bold flex items-center justify-between">
                  Throughput Speed
                  <Zap className="h-4 w-4 text-cortex-success" />
                </CardDescription>
                <CardTitle className="text-2xl font-bold mt-1 text-cortex-text">
                  {summary ? `${summary.avg_tokens_per_second.toFixed(1)} t/s` : "0.0 t/s"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-[10px] text-cortex-muted">Average generated speed</span>
              </CardContent>
            </Card>

            <Card className="border-cortex-border bg-cortex-surface/40 hover:bg-cortex-surface/60 transition duration-200">
              <CardHeader className="pb-2">
                <CardDescription className="text-xs uppercase tracking-wider text-cortex-muted font-bold flex items-center justify-between">
                  Task Cache Hits
                  <Layers className="h-4 w-4 text-cortex-accent" />
                </CardDescription>
                <CardTitle className="text-2xl font-bold mt-1 text-cortex-text">
                  {summary ? `${summary.cache_hit_rate_percent.toFixed(1)}%` : "0.0%"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-[10px] text-cortex-success">RAG Cache enabled</span>
              </CardContent>
            </Card>

            <Card className="border-cortex-border bg-cortex-surface/40 hover:bg-cortex-surface/60 transition duration-200">
              <CardHeader className="pb-2">
                <CardDescription className="text-xs uppercase tracking-wider text-cortex-muted font-bold flex items-center justify-between">
                  Total Request Logs
                  <Activity className="h-4 w-4 text-cortex-muted" />
                </CardDescription>
                <CardTitle className="text-2xl font-bold mt-1 text-cortex-text">
                  {summary ? summary.total_requests : 0}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <span className="text-[10px] text-cortex-muted">All-time inference sessions</span>
              </CardContent>
            </Card>
          </div>

          {/* Compute Usage + Most Used Models Grid */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Live resource meters */}
            <Card className="border-cortex-border bg-cortex-surface/40">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Cpu className="h-4.5 w-4.5 text-cortex-accent" />
                  Live Compute Hardware Load
                </CardTitle>
                <CardDescription>Real-time memory and processing load.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* System RAM */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-cortex-text font-semibold">System RAM Usage</span>
                    <span className="text-cortex-muted">
                      {summary ? `${summary.memory_usage.used_gb.toFixed(1)} GB / ${summary.memory_usage.total_gb.toFixed(0)} GB (${summary.memory_usage.usage_percent}%)` : "0 GB / 0 GB (0%)"}
                    </span>
                  </div>
                  <div className="w-full bg-cortex-border rounded-full h-2">
                    <div
                      className="bg-cortex-accent h-2 rounded-full transition-all duration-500"
                      style={{ width: `${summary ? summary.memory_usage.usage_percent : 0}%` }}
                    />
                  </div>
                </div>

                {/* GPU Util */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-cortex-text font-semibold">GPU Processing Core Load</span>
                    <span className="text-cortex-muted">
                      {summary ? `${summary.gpu_usage_percent.toFixed(0)}%` : "0%"}
                    </span>
                  </div>
                  <div className="w-full bg-cortex-border rounded-full h-2">
                    <div
                      className="bg-cortex-success h-2 rounded-full transition-all duration-500"
                      style={{ width: `${summary ? summary.gpu_usage_percent : 0}%` }}
                    />
                  </div>
                </div>

                {/* GPU VRAM */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-cortex-text font-semibold">GPU VRAM Memory Usage</span>
                    <span className="text-cortex-muted">
                      {summary ? `${summary.vram_usage.used_gb.toFixed(1)} GB / ${summary.vram_usage.total_gb.toFixed(1)} GB (${summary.vram_usage.usage_percent}%)` : "0.0 GB / 0.0 GB (0%)"}
                    </span>
                  </div>
                  <div className="w-full bg-cortex-border rounded-full h-2">
                    <div
                      className="bg-cortex-success h-2 rounded-full transition-all duration-500"
                      style={{ width: `${summary ? summary.vram_usage.usage_percent : 0}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Most Used Models */}
            <Card className="border-cortex-border bg-cortex-surface/40">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <HardDrive className="h-4.5 w-4.5 text-cortex-accent" />
                  Most Utilized Models
                </CardTitle>
                <CardDescription>Distribution of inference requests by model.</CardDescription>
              </CardHeader>
              <CardContent>
                {summary && summary.most_used_models.length > 0 ? (
                  <div className="space-y-4">
                    {summary.most_used_models.map((model, idx) => {
                      const totalRequests = summary.total_requests || 1;
                      const percent = Math.round((model.total_requests / totalRequests) * 100);
                      return (
                        <div key={`model-${idx}`} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <div>
                              <span className="font-semibold text-cortex-text block">{model.model_name}</span>
                              <span className="text-[10px] text-cortex-muted">{model.provider_name}</span>
                            </div>
                            <span className="text-cortex-muted text-right">
                              {model.total_requests} reqs ({percent}%)
                            </span>
                          </div>
                          <div className="w-full bg-cortex-border rounded-full h-1.5">
                            <div
                              className="bg-cortex-accent h-1.5 rounded-full"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex flex-col justify-center items-center h-48 text-center text-xs text-cortex-muted">
                    <Activity className="h-7 w-7 text-cortex-muted mb-2" />
                    <span>No request telemetry logged yet. Execute a chat query to record telemetry.</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* HEALTH TAB */}
      {activeTab === "health" && (
        <Card className="border-cortex-border bg-cortex-surface/40">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="h-4.5 w-4.5 text-cortex-success animate-pulse" />
              Local & API Model Health Status
            </CardTitle>
            <CardDescription>
              Health diagnostics based on success rate and latency metrics.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingHealth ? (
              <div className="flex justify-center items-center py-10">
                <Loader2 className="h-8 w-8 text-cortex-accent animate-spin" />
              </div>
            ) : health.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left border-collapse">
                  <thead>
                    <tr className="border-b border-cortex-border text-cortex-muted font-bold text-xs uppercase tracking-wider">
                      <th className="py-3 px-4">Model Name</th>
                      <th className="py-3 px-4">Provider</th>
                      <th className="py-3 px-4 text-center">Requests</th>
                      <th className="py-3 px-4 text-center">Success %</th>
                      <th className="py-3 px-4 text-center">Failure %</th>
                      <th className="py-3 px-4 text-right">Avg Latency</th>
                      <th className="py-3 px-4 text-center">Health</th>
                    </tr>
                  </thead>
                  <tbody>
                    {health.map((model, idx) => (
                      <tr key={`health-${idx}`} className="border-b border-cortex-border/50 hover:bg-cortex-elevated/20 transition">
                        <td className="py-3.5 px-4 font-semibold text-cortex-text truncate max-w-[200px]">{model.model_name}</td>
                        <td className="py-3.5 px-4 text-cortex-muted text-xs">{model.provider_name}</td>
                        <td className="py-3.5 px-4 text-center font-mono text-xs">{model.total_requests}</td>
                        <td className="py-3.5 px-4 text-center font-mono text-xs text-cortex-success">
                          {model.success_rate.toFixed(1)}%
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono text-xs text-cortex-warn">
                          {model.failure_rate.toFixed(1)}%
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono text-xs">{model.avg_latency_ms.toFixed(0)} ms</td>
                        <td className="py-3.5 px-4 text-center">
                          {model.status === "healthy" && (
                            <Badge className="bg-cortex-success/15 hover:bg-cortex-success/15 border border-cortex-success/30 text-cortex-success text-[10px]">
                              Healthy
                            </Badge>
                          )}
                          {model.status === "unstable" && (
                            <Badge className="bg-cortex-warn/15 hover:bg-cortex-warn/15 border border-cortex-warn/30 text-cortex-warn text-[10px]">
                              Unstable
                            </Badge>
                          )}
                          {model.status === "failing" && (
                            <Badge className="bg-red-500/15 hover:bg-red-500/15 border border-red-500/30 text-red-400 text-[10px]">
                              Failing
                            </Badge>
                          )}
                          {model.status === "inactive" && (
                            <Badge className="bg-cortex-elevated text-cortex-muted border-none text-[10px]">
                              Inactive
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex flex-col justify-center items-center h-48 text-center text-xs text-cortex-muted">
                <AlertTriangle className="h-8 w-8 text-cortex-warn mb-2" />
                <span>No health metrics recorded yet. Send chat queries to log health telemetry.</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ROUTING ANALYTICS TAB */}
      {activeTab === "routing" && (
        <div className="space-y-6">
          {/* Automatic vs Manual decisions */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="border-cortex-border bg-cortex-surface/40 md:col-span-1 flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shuffle className="h-4.5 w-4.5 text-cortex-accent" />
                  Routing Modes
                </CardTitle>
                <CardDescription>Auto router decisions vs manual overrides.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center py-6">
                {analytics && analytics.routing_mode.total > 0 ? (
                  <div className="space-y-6 w-full max-w-[200px]">
                    {/* Ring/Bar layout */}
                    <div className="flex justify-between items-center text-xs border-b border-cortex-border pb-2">
                      <span className="text-cortex-success font-semibold flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-cortex-success block" />
                        Auto Routed
                      </span>
                      <span className="font-mono font-bold text-cortex-text">
                        {analytics.routing_mode.auto} ({Math.round((analytics.routing_mode.auto / analytics.routing_mode.total) * 100)}%)
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-cortex-accent font-semibold flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-cortex-accent block" />
                        Manual Select
                      </span>
                      <span className="font-mono font-bold text-cortex-text">
                        {analytics.routing_mode.manual} ({Math.round((analytics.routing_mode.manual / analytics.routing_mode.total) * 100)}%)
                      </span>
                    </div>

                    <div className="w-full bg-cortex-border rounded-full h-3.5 flex overflow-hidden mt-4">
                      <div
                        className="bg-cortex-success h-3.5"
                        style={{ width: `${(analytics.routing_mode.auto / analytics.routing_mode.total) * 100}%` }}
                      />
                      <div
                        className="bg-cortex-accent h-3.5"
                        style={{ width: `${(analytics.routing_mode.manual / analytics.routing_mode.total) * 100}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-xs text-cortex-muted py-6">
                    No decisions recorded.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Profile distribution */}
            <Card className="border-cortex-border bg-cortex-surface/40 md:col-span-2">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="h-4.5 w-4.5 text-cortex-accent" />
                  Routing Profiles Share
                </CardTitle>
                <CardDescription>Relative usage share of router configuration profiles.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {analytics && analytics.profile_distribution.some(p => p.count > 0) ? (
                  analytics.profile_distribution.map((p, idx) => {
                    const total = analytics.routing_mode.total || 1;
                    const pct = Math.round((p.count / total) * 100);
                    return (
                      <div key={`profile-${idx}`} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-semibold text-cortex-text">{p.profile_name}</span>
                          <span className="text-cortex-muted font-mono">{pct}%</span>
                        </div>
                        <div className="w-full bg-cortex-border rounded-full h-2">
                          <div
                            className="bg-cortex-accent h-2 rounded-full"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="flex flex-col justify-center items-center h-32 text-center text-xs text-cortex-muted">
                    <span>No routing profile usage logged yet.</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Task Type Breakdown */}
          <Card className="border-cortex-border bg-cortex-surface/40">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Layers className="h-4.5 w-4.5 text-cortex-accent" />
                Task Type Distribution
              </CardTitle>
              <CardDescription>Breakdown of routed query categories, success rates, and latency.</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingAnalytics ? (
                <div className="flex justify-center items-center py-6">
                  <Loader2 className="h-8 w-8 text-cortex-accent animate-spin" />
                </div>
              ) : analytics && analytics.task_distribution.length > 0 ? (
                <div className="space-y-6">
                  {analytics.task_distribution.map((task, idx) => {
                    return (
                      <div key={`task-${idx}`} className="space-y-2">
                        <div className="flex flex-col sm:flex-row justify-between sm:items-center text-xs gap-1">
                          <div className="space-y-0.5">
                            <span className="font-bold text-cortex-text">{task.task_type}</span>
                            <span className="text-[10px] text-cortex-muted block">Key: {task.task_key}</span>
                          </div>
                          <div className="flex gap-4 text-[10px] text-cortex-muted">
                            <span>Requests: <strong className="text-cortex-text font-mono">{task.count}</strong></span>
                            <span>Success Rate: <strong className="text-cortex-success font-mono">{task.success_rate_percent.toFixed(0)}%</strong></span>
                            <span>Latency: <strong className="text-cortex-text font-mono">{task.avg_latency_ms.toFixed(0)}ms</strong></span>
                          </div>
                        </div>

                        {/* Visual Bar representation */}
                        <div className="w-full bg-cortex-border rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-cortex-accent to-cortex-success h-2 rounded-full"
                            style={{
                              width: `${Math.min(100, Math.max(10, (task.count / (analytics.routing_mode.total || 1)) * 100))}%`
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col justify-center items-center h-48 text-center text-xs text-cortex-muted">
                  <AlertTriangle className="h-8 w-8 text-cortex-warn mb-2" />
                  <span>No task category distribution logs. Query tasks to populate breakdown.</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* SETTINGS TAB */}
      {activeTab === "settings" && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Active routing profile */}
          <Card className="border-cortex-border bg-cortex-surface/40">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Shuffle className="h-4.5 w-4.5 text-cortex-accent" />
                Router Dispatch Profiles
              </CardTitle>
              <CardDescription>
                Switch ruleset mapping for automatic task routing.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3">
                {routingProfiles.length > 0 ? (
                  routingProfiles.map((profile) => {
                    const isActive = activeProfile.toLowerCase() === profile.name.toLowerCase();
                    return (
                      <button
                        type="button"
                        key={`profile-setting-${profile.name}`}
                        onClick={() => selectProfileMutation.mutate(profile.name)}
                        className={cn(
                          "flex items-center justify-between p-3.5 rounded-xl border text-left transition text-xs font-semibold cursor-pointer w-full",
                          isActive
                            ? "border-cortex-accent bg-cortex-accent-soft text-cortex-accent"
                            : "border-cortex-border bg-cortex-elevated/20 text-cortex-text hover:border-cortex-border-hover"
                        )}
                      >
                        <span>{profile.name} Ruleset</span>
                        {isActive && (
                          <Badge className="bg-cortex-accent text-cortex-bg border-none text-[9px] font-bold">
                            Active Ruleset
                          </Badge>
                        )}
                      </button>
                    );
                  })
                ) : (
                  <div className="text-xs text-cortex-muted">Loading profiles...</div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Model selector & privacy settings */}
          <Card className="border-cortex-border bg-cortex-surface/40">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Shield className="h-4.5 w-4.5 text-cortex-accent" />
                Default Fallback & Privacy Settings
              </CardTitle>
              <CardDescription>Manage core LLM behavior and data privacy rules.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Default Selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-cortex-text block">Default Fallback Model</label>
                <select
                  value={modelConfig.llm_model}
                  onChange={(e) => setModelConfig({ llm_model: e.target.value })}
                  className="w-full bg-cortex-bg border border-cortex-border rounded-xl px-3 py-2 text-xs text-cortex-text focus:outline-none focus:border-cortex-accent"
                >
                  <option value="">Select fallback model...</option>
                  {models.map((m: any) => (
                    <option key={m.id || m.name} value={m.name}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
                  {/* Fallback hardcoded if models empty */}
                  {models.length === 0 && (
                    <>
                      <option value="qwen2.5-coder:7b">qwen2.5-coder:7b (Ollama)</option>
                      <option value="llama3:8b">llama3:8b (Ollama)</option>
                    </>
                  )}
                </select>
                <span className="text-[10px] text-cortex-muted block">
                  Model utilized when task routing fails or is bypassed.
                </span>
              </div>

              <hr className="border-cortex-border/50" />

              {/* Switches */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-cortex-text block">Enforce Local-Only</span>
                    <span className="text-[10px] text-cortex-muted block">
                      Guarantees that no external API keys or cloud systems are touched.
                    </span>
                  </div>
                  <button
                    onClick={() => handleToggleLocalOnly(!localOnly)}
                    className={cn(
                      "w-10 h-5.5 rounded-full p-0.5 transition duration-200 focus:outline-none cursor-pointer shrink-0",
                      localOnly ? "bg-cortex-accent" : "bg-cortex-border"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4.5 h-4.5 rounded-full bg-cortex-bg transition duration-200 transform",
                        localOnly ? "translate-x-4.5" : "translate-x-0"
                      )}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-cortex-text block">Enable Cloud APIs</span>
                    <span className="text-[10px] text-cortex-muted block">
                      Enables high-capacity models (OpenAI, Claude) when high quality routing is active.
                    </span>
                  </div>
                  <button
                    onClick={() => handleToggleCloud(!cloudEnabled)}
                    className={cn(
                      "w-10 h-5.5 rounded-full p-0.5 transition duration-200 focus:outline-none cursor-pointer shrink-0",
                      cloudEnabled ? "bg-cortex-accent" : "bg-cortex-border"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4.5 h-4.5 rounded-full bg-cortex-bg transition duration-200 transform",
                        cloudEnabled ? "translate-x-4.5" : "translate-x-0"
                      )}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-cortex-text block">Enable Privacy Shield</span>
                    <span className="text-[10px] text-cortex-muted block">
                      Bypasses recording local chat metrics/telemetry entirely.
                    </span>
                  </div>
                  <button
                    onClick={() => handleTogglePrivacy(!privacyShield)}
                    className={cn(
                      "w-10 h-5.5 rounded-full p-0.5 transition duration-200 focus:outline-none cursor-pointer shrink-0",
                      privacyShield ? "bg-cortex-accent" : "bg-cortex-border"
                    )}
                  >
                    <div
                      className={cn(
                        "w-4.5 h-4.5 rounded-full bg-cortex-bg transition duration-200 transform",
                        privacyShield ? "translate-x-4.5" : "translate-x-0"
                      )}
                    />
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
