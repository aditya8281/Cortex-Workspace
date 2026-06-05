"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Modal, Input, Loader } from "../../src/shared/ui";

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}

function VaultSection({ label, count, sizeBytes, locked }) {
  return (
    <div className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12">
      <div className="flex items-center justify-between gap-cortex-12">
        <span className="font-mono text-sm uppercase tracking-[0.12em] text-cortex-text">{label}</span>
        <Badge variant={locked ? "warning" : "green"}>{locked ? "locked" : "open"}</Badge>
      </div>
      <div className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
        {count} files · {formatBytes(sizeBytes)}
      </div>
      <div className="h-1 overflow-hidden rounded-cortex bg-cortex-bg">
        <div className={`h-full rounded-cortex ${locked ? "bg-cortex-warning" : "bg-cortex-green"}`} style={{ width: "72%" }} />
      </div>
    </div>
  );
}

export default function VaultPage() {
  const [vault, setVault] = useState(null);
  const [locked, setLocked] = useState(true);
  const [unlocked, setUnlocked] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [unlocking, setUnlocking] = useState(false);
  const [unlockOpen, setUnlockOpen] = useState(false);

  const vaultUnlockedKey = "cortex_vault_unlocked";

  async function loadVault() {
    try {
      const response = await fetch("/api/vault", { cache: "no-store" });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "Vault request failed");
      }

      setVault(data);
      setLocked(window.sessionStorage.getItem(vaultUnlockedKey) !== "true");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Vault request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (typeof window !== "undefined" && window.sessionStorage.getItem(vaultUnlockedKey) === "true") {
      setUnlocked(true);
      setLocked(false);
    }
    loadVault();
    // Vault must start closed; the stored flag only affects presentation after explicit unlock.
  }, []);

  const sections = useMemo(() => {
    if (!vault?.categories) return [];
    return Object.entries(vault.categories).map(([label, stats]) => ({
      label,
      count: stats.file_count || 0,
      sizeBytes: stats.size_bytes || 0,
    }));
  }, [vault]);

  async function submitUnlock(event) {
    event.preventDefault();
    if (!password.trim()) {
      setError("SYSTEM ERROR: Password is required.");
      return;
    }

    setUnlocking(true);
    setError("");

    try {
      const response = await fetch("/api/vault", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || "Vault unlock failed");
      }

      setUnlocked(true);
      setLocked(false);
      window.sessionStorage.setItem(vaultUnlockedKey, "true");
      setVault(data);
      setUnlockOpen(false);
      setPassword("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Vault unlock failed");
    } finally {
      setUnlocking(false);
    }
  }

  function lockVault() {
    setUnlocked(false);
    setLocked(true);
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(vaultUnlockedKey);
    }
  }

  return (
    <section className="grid gap-cortex-16">
      <div className="flex items-start justify-between gap-cortex-16">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Vault</p>
          <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Encrypted Vault Control</h1>
          <p className="mt-cortex-8 max-w-2xl text-sm leading-6 text-cortex-text-muted">
            Secure storage surface with locked sections and password-gated unlock. The vault never opens by default.
          </p>
        </div>
        <div className="flex items-center gap-cortex-12">
          <Badge variant="warning">{locked ? "locked" : "unlocked"}</Badge>
          <Badge variant="cyan">encrypted</Badge>
          <Button variant="secondary" size="sm" onClick={() => setUnlockOpen(true)}>
            {loading ? (
              <span className="inline-flex items-center gap-cortex-8">
                <Loader className="h-3.5 w-3.5" />
                Syncing
              </span>
            ) : locked ? (
              "Unlock vault"
            ) : (
              "Re-authenticate"
            )}
          </Button>
        </div>
      </div>

      {error ? (
        <Card className="border-cortex-error/45 bg-cortex-error/10 text-cortex-error">
          <div className="font-mono text-sm">Error: {error}</div>
        </Card>
      ) : null}

      <div className="grid gap-cortex-16 xl:grid-cols-[minmax(0,1.4fr)_360px]">
        <Card className="grid gap-cortex-16">
          <div className="flex items-center justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Protected sections</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Vault sectors</h2>
            </div>
            <Badge variant={unlocked ? "green" : "warning"}>{unlocked ? "session open" : "sealed"}</Badge>
          </div>

          <div className="grid gap-cortex-12">
            {sections.length > 0 ? (
              sections.map((section) => (
                <VaultSection
                  key={section.label}
                  label={section.label}
                  count={section.count}
                  sizeBytes={section.sizeBytes}
                  locked={!unlocked}
                />
              ))
            ) : (
              <div className="rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
                Vault metadata unavailable.
              </div>
            )}
          </div>
        </Card>

        <div className="grid gap-cortex-16">
          <Card className="grid gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Status</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Encrypted indicator</h2>
            </div>
            <div className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-sm text-cortex-text-muted">
              <div className="flex items-center justify-between">
                <span>Access state</span>
                <span className="text-cortex-text">{locked ? "locked" : "unlocked"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Paused indexing</span>
                <span className="text-cortex-text">{vault?.is_paused ? "yes" : "no"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Vault path</span>
                <span className="truncate text-cortex-text">{vault?.active_path || "unknown"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Total size</span>
                <span className="text-cortex-text">{formatBytes(vault?.total_size_bytes || 0)}</span>
              </div>
            </div>
          </Card>

          <Card className="grid gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">Controls</p>
              <h2 className="mt-cortex-8 text-lg font-medium text-cortex-text">Session actions</h2>
            </div>
            <div className="grid gap-cortex-8">
              <Button variant="primary" onClick={() => setUnlockOpen(true)}>
                {locked ? "Unlock vault" : "Re-open modal"}
              </Button>
              <Button variant="secondary" onClick={lockVault} disabled={!unlocked}>
                Lock session
              </Button>
            </div>
          </Card>
        </div>
      </div>

      <Modal
        open={unlockOpen}
        onClose={() => setUnlockOpen(false)}
        title="Vault unlock required"
        footer={
          <Button type="submit" variant="primary" form="vault-unlock-form" disabled={unlocking}>
            {unlocking ? "Verifying..." : "Unlock"}
          </Button>
        }
      >
        <form id="vault-unlock-form" className="grid gap-cortex-12" onSubmit={submitUnlock}>
          <div className="rounded-cortex border border-cortex-warning/30 bg-cortex-warning/10 p-cortex-12 font-mono text-xs uppercase tracking-[0.12em] text-cortex-warning">
            The vault remains locked until password verification completes.
          </div>
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter account password"
            autoComplete="current-password"
          />
        </form>
      </Modal>
    </section>
  );
}
