"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Settings, Save, Eye, EyeOff, Download } from "lucide-react";
import Button from "../../src/shared/ui/Button";
import Card from "../../src/shared/ui/Card";
import { cn } from "../../src/lib/utils";
import { toast } from "sonner";
import { api } from "../../src/shared/api/client";

interface LLMSettings {
  inference_backend: string;
  huggingface_token: string;
  auto_download: boolean;
  max_concurrent_downloads: number;
}

export default function LLMSettingsForm() {
  const [settings, setSettings] = useState<LLMSettings>({
    inference_backend: "auto",
    huggingface_token: "",
    auto_download: true,
    max_concurrent_downloads: 2,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    try {
      const data = await api.get<LLMSettings>("/api/v1/models/settings");
      setSettings(data);
    } catch (err) {
      console.error("Failed to load LLM settings:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await api.put("/api/v1/models/settings", settings);
      toast.success("LLM settings saved");
    } catch (err) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <Card gradient className="p-5">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-bg-elevated rounded w-1/4" />
          <div className="h-10 bg-bg-elevated rounded" />
          <div className="h-10 bg-bg-elevated rounded" />
        </div>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <Card gradient className="p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-9 w-9 rounded-lg bg-accent/10 border border-accent/15 flex items-center justify-center">
            <Settings className="h-4.5 w-4.5 text-accent" />
          </div>
          <div>
            <h2 className="text-sm font-medium text-text">LLM Configuration</h2>
            <p className="text-xs text-text-muted">Configure inference backend and model settings</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Inference Backend</label>
            <div className="flex rounded-xl bg-bg-surface p-1 border border-border/50">
              {(["auto", "ollama", "llama.cpp", "openai"]).map((backend) => (
                <button
                  key={backend}
                  onClick={() => setSettings({ ...settings, inference_backend: backend })}
                  className={cn(
                    "flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors",
                    settings.inference_backend === backend
                      ? "bg-bg-elevated text-text border border-border shadow-sm"
                      : "text-text-muted hover:text-text-secondary"
                  )}
                >
                  {backend === "auto" ? "Auto" : backend === "ollama" ? "Ollama" : backend === "llama.cpp" ? "llama.cpp" : "OpenAI"}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">HuggingFace Token</label>
            <div className="relative">
              <input
                type={showToken ? "text" : "password"}
                value={settings.huggingface_token}
                onChange={(e) => setSettings({ ...settings, huggingface_token: e.target.value })}
                placeholder="hf_..."
                className="w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 pr-10 text-sm text-text placeholder:text-text-muted outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
              />
              <button
                type="button"
                onClick={() => setShowToken(!showToken)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text"
              >
                {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-text-muted" />
              <span className="text-sm text-text">Auto-download models</span>
            </div>
            <button
              role="switch"
              aria-checked={settings.auto_download}
              onClick={() => setSettings({ ...settings, auto_download: !settings.auto_download })}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSettings({ ...settings, auto_download: !settings.auto_download });
                }
              }}
              className={cn(
                "relative w-10 h-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent/40",
                settings.auto_download ? "bg-accent" : "bg-bg-elevated"
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform",
                  settings.auto_download ? "left-[22px]" : "left-0.5"
                )}
              />
            </button>
          </div>

          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-text-secondary">Max Concurrent Downloads</label>
            <input
              type="number"
              min={1}
              max={5}
              value={settings.max_concurrent_downloads}
              onChange={(e) => {
                const val = parseInt(e.target.value) || 2;
                setSettings({ ...settings, max_concurrent_downloads: Math.min(5, Math.max(1, val)) });
              }}
              className="w-24 rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
            />
          </div>

          <div className="flex justify-end pt-2">
            <Button size="sm" loading={saving} onClick={handleSave}>
              <Save className="h-3.5 w-3.5 mr-1.5" />
              Save Settings
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
