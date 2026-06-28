"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Badge } from "@/shared/ui/Badge";
import { StatusDot } from "@/shared/ui/StatusDot";
import { settingsApi, type UserProfile } from "./api";

export default function SettingsPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [vaultLocked, setVaultLocked] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadProfile = useCallback(async () => {
    try {
      const data = await settingsApi.getProfile();
      setProfile(data);
      setUsername(data.username);
      setEmail(data.email);
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
    try {
      await settingsApi.updateProfile({ username, email });
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="space-y-6 max-w-2xl">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Settings</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Manage your account and system preferences
          </p>
        </div>

        {/* Profile */}
        <Card className="p-5">
          <h2 className="text-title font-semibold text-text-primary mb-4">Profile</h2>
          <div className="space-y-4">
            <Input
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <div className="flex justify-end">
              <Button onClick={handleSave} loading={saving}>
                Save Changes
              </Button>
            </div>
          </div>
        </Card>

        {/* Vault Status */}
        <Card className="p-5">
          <h2 className="text-title font-semibold text-text-primary mb-4">Vault</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <StatusDot color={vaultLocked ? "warning" : "success"} />
              <div>
                <p className="text-sm font-medium text-text-primary">
                  {vaultLocked ? "Vault Locked" : "Vault Unlocked"}
                </p>
                <p className="text-xs text-text-muted">
                  Encrypted file storage for sensitive data
                </p>
              </div>
            </div>
            <Badge variant={vaultLocked ? "warning" : "success"}>
              {vaultLocked ? "Locked" : "Unlocked"}
            </Badge>
          </div>
        </Card>

        {/* Privacy */}
        <Card className="p-5">
          <h2 className="text-title font-semibold text-text-primary mb-4">Privacy</h2>
          <p className="text-sm text-text-secondary mb-3">
            Control what data CORTEX collects and processes locally.
          </p>
          <div className="space-y-2">
            <div className="flex items-center justify-between py-2 border-b border-border-subtle">
              <div>
                <p className="text-sm text-text-primary">Telemetry</p>
                <p className="text-xs text-text-muted">Anonymous usage stats</p>
              </div>
              <Badge variant="default">Disabled</Badge>
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm text-text-primary">Data Processing</p>
                <p className="text-xs text-text-muted">Local processing only</p>
              </div>
              <Badge variant="success">Local</Badge>
            </div>
          </div>
        </Card>

        {/* Account */}
        <Card className="p-5">
          <h2 className="text-title font-semibold text-text-primary mb-4">Account</h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-primary">Sign out of your account</p>
              <p className="text-xs text-text-muted">
                You&apos;ll need to sign in again next time
              </p>
            </div>
            <Button variant="danger" size="sm" onClick={logout}>
              Sign Out
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
