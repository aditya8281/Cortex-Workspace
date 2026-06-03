import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/stores/appStore";
import { useAutomationSettings, useUpdateAutomation } from "@/hooks/useIntelligence";
import { getUserSettings, updateUserSettings } from "@/api/ai";
import { login, register, getMe, logout } from "@/api/auth";
import { useEffect } from "react";

export function SettingsPage() {
  const token = useAppStore((s) => s.token);
  const setToken = useAppStore((s) => s.setToken);
  const currentUser = useAppStore((s) => s.currentUser);
  const setCurrentUser = useAppStore((s) => s.setCurrentUser);
  const modelConfig = useAppStore((s) => s.modelConfig);
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

  useEffect(() => {
    if (!token) return;
    void getMe().then(setCurrentUser).catch(() => setToken(null));
    void getUserSettings().then((s) => {
      setApiBaseUrl(s.api_base_url || "");
      if (s.api_key_masked) setApiKey(s.api_key_masked);
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

  return (
    <div className="h-full overflow-y-auto p-6 md:p-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <h2 className="text-xl font-semibold">Settings</h2>

        <Card>
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

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder="LLM model"
              value={modelConfig.llm_model}
              onChange={(e) => setModelConfig({ llm_model: e.target.value })}
            />
            <Input
              placeholder="Inference engine (Ollama / API)"
              value={modelConfig.inference_engine}
              onChange={(e) => setModelConfig({ inference_engine: e.target.value })}
            />
          </CardContent>
        </Card>

        <Card>
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
                )
              }
            >
              Save credentials
            </Button>
          </CardContent>
        </Card>

        <Card>
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
