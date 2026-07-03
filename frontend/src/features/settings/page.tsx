"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";

import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Badge } from "@/shared/ui/Badge";
import { StatusDot } from "@/shared/ui/StatusDot";
import { settingsApi, type UserProfile } from "./api";
import { Skeleton } from "@/shared/ui/Skeleton";
import { useToast } from "@/shared/ui/Toast";

export default function SettingsPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [username, setUsername] = useState("");
  const [nickname, setNickname] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [vaultLocked, setVaultLocked] = useState(true);
  const [activeTab, setActiveTab] = useState<"profile" | "vault" | "privacy" | "account">("profile");
  const { toast } = useToast();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadProfile = useCallback(async () => {
    try {
      const data = await settingsApi.getProfile();
      setProfile(data);
      setUsername(data.username ?? "");
      setNickname(data.nickname ?? "");
      setBio(data.bio ?? "");
    } catch {
      // ignore
    }
  }, []);

  const loadVault = useCallback(async () => {
    try {
      const data = await settingsApi.getVaultStatus();
      setVaultLocked(data.locked);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadProfile();
    loadVault();
  }, [loadProfile, loadVault]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await settingsApi.updateProfile({ nickname, bio });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      toast("Failed to save profile", "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !user) return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl space-y-6">
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-4 w-48" />
        <div className="flex gap-0.5 p-0.5 rounded-lg bg-bg-surface border border-border-subtle">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-8 flex-1 rounded-md" />
          ))}
        </div>
        <Card className="p-5">
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-10 w-32 rounded-md ml-auto" />
          </div>
        </Card>
      </div>
    </div>
  );

  const tabs = [
    { key: "profile" as const, label: "Profile" },
    { key: "vault" as const, label: "Vault" },
    { key: "privacy" as const, label: "Privacy" },
    { key: "account" as const, label: "Account" },
  ];

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl animate-fade-in">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-headline font-semibold text-text-primary">Settings</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Manage your account, vault, and privacy preferences
          </p>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-0.5 mb-6 p-0.5 rounded-lg bg-bg-surface border border-border-subtle">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-md motion-safe:transition-all motion-safe:duration-150 ${
                tab.key === activeTab
                  ? "bg-accent/12 text-accent"
                  : "text-text-muted hover:text-text-secondary hover:bg-bg-elevated"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Profile Tab */}
        {activeTab === "profile" && (
          <div className="space-y-5">
            <Card className="p-5">
              <div className="flex items-center gap-3 mb-5">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/12 text-accent text-lg font-semibold">
                  {username.charAt(0).toUpperCase() || "U"}
                </div>
                <div>
                  <h2 className="text-title font-semibold text-text-primary">
                    {profile?.username ?? "User"}
                  </h2>
                  <p className="text-xs text-text-muted">
                    Member since {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : "—"}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <Input
                  label="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  maxLength={32}
                  required
                  aria-required="true"
                />
                <Input
                  label="Nickname"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="What should we call you?"
                  maxLength={64}
                />
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">
                    Bio
                  </label>
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={3}
                    maxLength={512}
                    placeholder="Tell us about yourself"
                    className="w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/25 motion-safe:transition-colors motion-safe:duration-150"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  {saved && (
                    <span className="text-xs text-success self-center">Saved</span>
                  )}
                  <Button onClick={handleSave} loading={saving}>
                    Save Changes
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Vault Tab */}
        {activeTab === "vault" && (
          <div className="space-y-5">
            <Card className="p-5">
              <h2 className="text-title font-semibold text-text-primary mb-1">
                Encrypted Vault
              </h2>
              <p className="text-xs text-text-muted mb-4">
                Your vault password encrypts personal data locally. It cannot be recovered if lost.
              </p>
              <div className="flex items-center justify-between py-3 px-3.5 rounded-lg bg-bg-surface border border-border-subtle">
                <div className="flex items-center gap-2.5">
                  <StatusDot color={vaultLocked ? "warning" : "success"} size="sm" />
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      {vaultLocked ? "Vault Locked" : "Vault Unlocked"}
                    </p>
                    <p className="text-xs text-text-muted">
                      {vaultLocked
                        ? "Enter your vault password to unlock"
                        : "Your encrypted storage is accessible"}
                    </p>
                  </div>
                </div>
                <Badge variant={vaultLocked ? "warning" : "success"}>
                  {vaultLocked ? "Locked" : "Unlocked"}
                </Badge>
              </div>
              <div className="mt-4">
                <a
                  href="/vault"
                  className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:text-accent/80 motion-safe:transition-colors motion-safe:duration-150"
                >
                  Open Vault
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M2.5 6h7m0 0L6.5 3m3 3L6.5 9" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </a>
              </div>
            </Card>
          </div>
        )}

        {/* Privacy Tab */}
        {activeTab === "privacy" && (
          <div className="space-y-5">
            <Card className="p-5">
              <h2 className="text-title font-semibold text-text-primary mb-1">
                Privacy Controls
              </h2>
              <p className="text-xs text-text-muted mb-4">
                Control what data CORTEX collects and processes. All processing happens locally.
              </p>
              <div className="space-y-0">
                {[
                  { label: "Telemetry", desc: "Anonymous usage statistics", status: "Disabled", variant: "default" as const },
                  { label: "Data Processing", desc: "Local-only inference and analysis", status: "Local", variant: "success" as const },
                  { label: "Encryption at Rest", desc: "AES-256 for stored data", status: "Active", variant: "success" as const },
                  { label: "Network Isolation", desc: "No data leaves your machine", status: "Enforced", variant: "success" as const },
                ].map((item, i) => (
                  <div
                    key={item.label}
                    className={`flex items-center justify-between py-3 ${
                      i < 3 ? "border-b border-border-subtle" : ""
                    }`}
                  >
                    <div>
                      <p className="text-sm text-text-primary">{item.label}</p>
                      <p className="text-xs text-text-muted">{item.desc}</p>
                    </div>
                    <Badge variant={item.variant}>{item.status}</Badge>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5">
              <a
                href="/privacy"
                className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:text-accent/80 motion-safe:transition-colors motion-safe:duration-150"
              >
                Advanced Privacy Settings
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M2.5 6h7m0 0L6.5 3m3 3L6.5 9" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </a>
            </Card>
          </div>
        )}

        {/* Account Tab */}
        {activeTab === "account" && (
          <div className="space-y-5">
            <Card className="p-5">
              <h2 className="text-title font-semibold text-text-primary mb-1">
                Account Details
              </h2>
              <p className="text-xs text-text-muted mb-4">
                Your account information and session management.
              </p>
              <div className="space-y-3">
                {[
                  { label: "Username", value: user.username },
                  { label: "User ID", value: String(user.id) },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-2.5 px-3.5 rounded-lg bg-bg-surface">
                    <span className="text-xs text-text-muted">{item.label}</span>
                    <span className="text-sm font-mono text-text-secondary">{item.value}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-5">
              <h2 className="text-title font-semibold text-text-danger mb-1">
                Sign Out
              </h2>
              <p className="text-xs text-text-muted mb-4">
                You&apos;ll need to sign in again next time.
              </p>
              <Button variant="danger" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
