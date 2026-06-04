import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/stores/appStore";
import { useAutomationSettings, useUpdateAutomation } from "@/hooks/useIntelligence";
import {
  getUserSettings,
  updateUserSettings,
  getVaultSettings,
  changeVaultPath,
  resetVault,
  exportVault,
  importVault,
  type VaultSettings
} from "@/api/ai";
import { login, register, getMe, logout } from "@/api/auth";
import { Folder, Download, Upload, Trash2, Loader2 } from "lucide-react";

export function SettingsPage() {
  const token = useAppStore((s) => s.token);
  const setToken = useAppStore((s) => s.setToken);
  const currentUser = useAppStore((s) => s.currentUser);
  const setCurrentUser = useAppStore((s) => s.setCurrentUser);
  const setModelConfig = useAppStore((s) => s.setModelConfig);
  const apiBaseUrl = useAppStore((s) => s.apiBaseUrl);
  const apiKey = useAppStore((s) => s.apiKey);
  const setApiBaseUrl = useAppStore((s) => s.setApiBaseUrl);
  const setApiKey = useAppStore((s) => s.setApiKey);
  const setToast = useAppStore((s) => s.setToast);

  const { data: automation } = useAutomationSettings();
  const updateAutomation = useUpdateAutomation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");

  // Model preferences state
  const [llmModel, setLlmModel] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [vectorDb, setVectorDb] = useState("");
  const [inferenceEngine, setInferenceEngine] = useState("");
  const [codeParsing, setCodeParsing] = useState("");

  // Vault state
  const [vaultSettings, setVaultSettings] = useState<VaultSettings | null>(null);
  const [newVaultPath, setNewVaultPath] = useState("");
  const [loadingVault, setLoadingVault] = useState(false);
  const [migrating, setMigrating] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);

  const loadVaultSettings = async () => {
    try {
      setLoadingVault(true);
      const data = await getVaultSettings();
      setVaultSettings(data);
      setNewVaultPath(data.active_path);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingVault(false);
    }
  };

  useEffect(() => {
    // Load vault settings on load regardless of token (local mode fallback)
    void loadVaultSettings();

    if (!token) return;
    void getMe().then(setCurrentUser).catch(() => setToken(null));
    void getUserSettings().then((s) => {
      setApiBaseUrl(s.api_base_url || "");
      if (s.api_key_masked) setApiKey(s.api_key_masked);
      setLlmModel(s.llm_model || "");
      setEmbeddingModel(s.embedding_model || "");
      setVectorDb(s.vector_db || "");
      setInferenceEngine(s.inference_engine || "");
      setCodeParsing(s.code_parsing || "");
    });
  }, [token, setCurrentUser, setToken, setApiBaseUrl, setApiKey]);

  const handleAuth = async () => {
    try {
      if (authMode === "register") {
        await register(email, "Cortex User", password);
        const res = await login(email, password);
        setToken(res.access_token);
      } else {
        const res = await login(email, password);
        setToken(res.access_token);
      }
      setToast("Signed in");
    } catch {
      setToast("Authentication failed");
    }
  };

  const handleMigrate = async () => {
    if (!newVaultPath) return;
    try {
      setMigrating(true);
      const res = await changeVaultPath(newVaultPath);
      setToast(res.message);
      await loadVaultSettings();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Migration failed";
      setToast(`Migration failed: ${msg}`);
    } finally {
      setMigrating(false);
    }
  };

  const handleReset = async () => {
    const doubleConfirm = confirm(
      "CRITICAL WARNING: This will permanently delete all local memory, embeddings, databases, and caches! This action cannot be undone.\n\nAre you absolutely sure you want to perform a vault reset?"
    );
    if (!doubleConfirm) return;

    try {
      setResetting(true);
      const res = await resetVault();
      setToast(res.message);
      await loadVaultSettings();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Reset failed";
      setToast(`Reset failed: ${msg}`);
    } finally {
      setResetting(false);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const blob = await exportVault();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "cortex_brain_vault_backup.zip");
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      setToast("Backup ZIP exported successfully");
    } catch (e) {
      console.error(e);
      setToast("Export failed");
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const doubleConfirm = confirm(
      "WARNING: Restoring from a backup will overwrite your current memory vault completely.\n\nDo you want to proceed?"
    );
    if (!doubleConfirm) return;

    try {
      setImporting(true);
      const res = await importVault(file);
      setToast(res.message);
      await loadVaultSettings();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Import failed";
      setToast(`Import failed: ${msg}`);
    } finally {
      setImporting(false);
      e.target.value = "";
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8 bg-cortex-bg">
      <div className="mx-auto max-w-2xl space-y-6">
        <h2 className="text-xl font-bold text-cortex-text">Settings</h2>

        {/* Account settings */}
        <Card className="border-cortex-border bg-cortex-surface/50">
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
            <CardDescription>
              {currentUser ? `${currentUser.full_name} (${currentUser.email})` : "Local mode — sign in to sync memory"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!token ? (
              <>
                <div className="flex gap-2">
                  <Button variant={authMode === "login" ? "default" : "secondary"} size="sm" onClick={() => setAuthMode("login")}>
                    Login
                  </Button>
                  <Button variant={authMode === "register" ? "default" : "secondary"} size="sm" onClick={() => setAuthMode("register")}>
                    Register
                  </Button>
                </div>
                <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
                <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                <Button onClick={() => void handleAuth()}>Continue</Button>
              </>
            ) : (
              <Button variant="secondary" onClick={() => { logout(); setToken(null); setCurrentUser(null); }}>
                Sign out
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Brain Vault settings */}
        <Card className="border-cortex-border bg-cortex-surface/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Folder className="h-4 w-4 text-cortex-accent" />
              Cortex Brain Vault
            </CardTitle>
            <CardDescription>
              Manage the self-contained directory containing all cortex memory, databases, caches, and sync states.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-cortex-text">Vault Storage Root Path</label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. ~/cortex_memory"
                  value={newVaultPath}
                  onChange={(e) => setNewVaultPath(e.target.value)}
                  disabled={migrating}
                />
                <Button
                  variant="secondary"
                  disabled={migrating || !newVaultPath || newVaultPath === vaultSettings?.active_path}
                  onClick={handleMigrate}
                  className="shrink-0"
                >
                  {migrating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Migrate"}
                </Button>
              </div>
              <p className="text-[11px] text-cortex-muted">
                System paths (e.g. <code>/etc</code>, <code>/sys</code>) are blocked for safety. Content will be copied automatically with no data loss.
              </p>
            </div>

            {loadingVault ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-cortex-accent" />
              </div>
            ) : vaultSettings ? (
              <div className="rounded-2xl border border-cortex-border bg-cortex-elevated/40 p-4 space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-cortex-muted">Vault Size:</span>
                  <span className="text-cortex-text">{(vaultSettings.total_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-cortex-muted">Indexing Status:</span>
                  <Badge variant={vaultSettings.is_paused ? "default" : "accent"}>
                    {vaultSettings.is_paused ? "Paused" : "Active"}
                  </Badge>
                </div>

                <div className="pt-2 border-t border-cortex-border space-y-1 text-xs">
                  <span className="font-semibold text-cortex-text text-[11px] uppercase tracking-wider">Subfolders</span>
                  {Object.entries(vaultSettings.categories).map(([cat, stats]) => (
                    <div key={cat} className="flex justify-between text-[11px] text-cortex-muted">
                      <span>{cat}/</span>
                      <span>
                        {stats.file_count} files ({(stats.size_bytes / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="pt-3 border-t border-cortex-border flex flex-wrap gap-2">
              <Button
                variant="secondary"
                size="sm"
                className="gap-2"
                onClick={handleExport}
                disabled={exporting}
              >
                <Download className="h-3.5 w-3.5" />
                {exporting ? "Exporting..." : "Backup Export (ZIP)"}
              </Button>

              <div className="relative">
                <input
                  type="file"
                  id="vault-import-input"
                  accept=".zip"
                  onChange={handleImport}
                  className="hidden"
                  disabled={importing}
                />
                <Button
                  variant="secondary"
                  size="sm"
                  className="gap-2"
                  onClick={() => document.getElementById("vault-import-input")?.click()}
                  disabled={importing}
                >
                  <Upload className="h-3.5 w-3.5" />
                  {importing ? "Importing..." : "Restore Import (ZIP)"}
                </Button>
              </div>

              <Button
                variant="destructive"
                size="sm"
                className="gap-2 ml-auto"
                onClick={handleReset}
                disabled={resetting}
              >
                <Trash2 className="h-3.5 w-3.5" />
                {resetting ? "Resetting..." : "Reset Vault"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Model preference card */}
        <Card className="border-cortex-border bg-cortex-surface/50">
          <CardHeader>
            <CardTitle className="text-base">Model Preferences</CardTitle>
            <CardDescription>Persist model preference profiles in your Cortex account.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-xs text-cortex-muted">LLM Model</label>
              <Input placeholder="e.g. qwen3:8b, gpt-4o-mini" value={llmModel} onChange={(e) => setLlmModel(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-xs text-cortex-muted">Embedding Model</label>
              <Input placeholder="e.g. all-minilm-l6-v2" value={embeddingModel} onChange={(e) => setEmbeddingModel(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-xs text-cortex-muted">Vector DB</label>
              <Input placeholder="e.g. chromadb, faiss" value={vectorDb} onChange={(e) => setVectorDb(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-xs text-cortex-muted">Inference Engine</label>
              <Input placeholder="e.g. Ollama, OpenAI" value={inferenceEngine} onChange={(e) => setInferenceEngine(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-xs text-cortex-muted">Code Parsing Engine</label>
              <Input placeholder="e.g. tree-sitter, regex" value={codeParsing} onChange={(e) => setCodeParsing(e.target.value)} className="mt-1" />
            </div>
            <Button
              variant="secondary"
              onClick={() =>
                void updateUserSettings({
                  llm_model: llmModel,
                  embedding_model: embeddingModel,
                  vector_db: vectorDb,
                  inference_engine: inferenceEngine,
                  code_parsing: codeParsing,
                }).then((s) => {
                  setToast("Model preferences saved");
                  setModelConfig({
                    llm_model: s.llm_model || "",
                    embedding_model: s.embedding_model || "",
                    vector_db: s.vector_db || "",
                    inference_engine: s.inference_engine || "",
                    code_parsing: s.code_parsing || "",
                  });
                }).catch(() => setToast("Must be signed in to save preferences"))
              }
            >
              Save preferences
            </Button>
          </CardContent>
        </Card>

        {/* API Credentials */}
        <Card className="border-cortex-border bg-cortex-surface/50">
          <CardHeader>
            <CardTitle className="text-base">API credentials</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="API base URL" value={apiBaseUrl} onChange={(e) => setApiBaseUrl(e.target.value)} />
            <Input placeholder="API key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} type="password" />
            <Button
              variant="secondary"
              onClick={() =>
                void updateUserSettings({ api_base_url: apiBaseUrl, api_key: apiKey }).then(() =>
                  setToast("Credentials saved"),
                ).catch(() => setToast("Must be signed in to save credentials"))
              }
            >
              Save credentials
            </Button>
          </CardContent>
        </Card>

        {/* Automation & Permissions */}
        <Card className="border-cortex-border bg-cortex-surface/50">
          <CardHeader>
            <CardTitle className="text-base">Automation & permissions</CardTitle>
            <CardDescription>Control what Cortex can do without asking.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(["observation", "approval", "trusted"] as const).map((level) => (
              <div key={level} className="rounded-lg border border-cortex-border p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium capitalize">{level}</span>
                  {automation?.automation_level === level && <Badge variant="accent">Active</Badge>}
                </div>
                <p className="mt-1 text-xs text-cortex-muted">
                  {level === "observation" && "Read-only. No modifications without explicit approval."}
                  {level === "approval" && "Default. Cortex plans changes and waits for confirmation."}
                  {level === "trusted" && "Auto-run trusted categories; destructive actions still need approval."}
                </p>
                <Button
                  size="sm"
                  variant="secondary"
                  className="mt-2"
                  onClick={() => updateAutomation.mutate({ automation_level: level })}
                >
                  Enable
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
