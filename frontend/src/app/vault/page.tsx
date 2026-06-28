"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Modal } from "@/shared/ui/Modal";
import { StatusDot } from "@/shared/ui/StatusDot";
import { vault, type VaultStatus, type VaultFile } from "@/features/privacy/api";

export default function VaultPage() {
  const [status, setStatus] = useState<VaultStatus | null>(null);
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unlockOpen, setUnlockOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [unlocking, setUnlocking] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await vault.status();
      setStatus(s);
      if (!s.locked) {
        const f = await vault.files();
        setFiles(f.items);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleUnlock = async () => {
    if (!password.trim()) return;
    setUnlocking(true);
    try {
      await vault.unlock({ password });
      setUnlockOpen(false);
      setPassword("");
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUnlocking(false);
    }
  };

  const handleLock = async () => {
    try {
      await vault.lock();
      setFiles([]);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <AppShell>
      <div className="max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">Encrypted Vault</h1>
            <p className="text-sm text-text-secondary mt-1">Fernet-encrypted per-user file storage</p>
          </div>
          {status && (
            <div className="flex items-center gap-2">
              <StatusDot color={status.locked ? "warning" : "success"} />
              <span className="text-sm text-text-secondary">{status.locked ? "Locked" : "Unlocked"}</span>
              {status.locked ? (
                <Button size="sm" onClick={() => setUnlockOpen(true)}>Unlock</Button>
              ) : (
                <Button size="sm" variant="ghost" onClick={handleLock}>Lock</Button>
              )}
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {/* Stats */}
        {status && !status.locked && (
          <div className="grid grid-cols-3 gap-3 mb-6">
            <Card className="p-4 text-center">
              <p className="text-headline font-semibold text-text-primary">{status.file_count}</p>
              <p className="text-xs text-text-muted mt-1">Files</p>
            </Card>
            <Card className="p-4 text-center">
              <p className="text-headline font-semibold text-text-primary">{formatBytes(status.total_size)}</p>
              <p className="text-xs text-text-muted mt-1">Total Size</p>
            </Card>
            <Card className="p-4 text-center">
              <p className="text-headline font-semibold text-text-primary">
                {status.last_accessed ? new Date(status.last_accessed).toLocaleDateString() : "Never"}
              </p>
              <p className="text-xs text-text-muted mt-1">Last Accessed</p>
            </Card>
          </div>
        )}

        {/* Files */}
        {status && !status.locked && (
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-text-primary mb-3">Files</h2>
            {files.length === 0 ? (
              <Card className="p-8 text-center">
                <p className="text-sm text-text-secondary">No files in vault yet</p>
              </Card>
            ) : (
              files.map(f => (
                <Card key={f.path} className="p-3 flex items-center gap-3">
                  <div className="h-8 w-8 rounded-md bg-bg-surface flex items-center justify-center flex-shrink-0">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted">
                      <path d="M3 1h5l3 3v8a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" />
                    </svg>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-text-primary truncate">{f.name}</p>
                    <p className="text-xs text-text-muted">{formatBytes(f.size)} · {f.mime_type}</p>
                  </div>
                  <span className="text-xs text-text-muted whitespace-nowrap">
                    {new Date(f.modified_at).toLocaleDateString()}
                  </span>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Locked State */}
        {status && status.locked && !loading && (
          <Card className="p-12 text-center">
            <div className="h-12 w-12 rounded-xl bg-bg-surface flex items-center justify-center mx-auto mb-4">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted">
                <rect x="3" y="9" width="14" height="9" rx="2" />
                <path d="M6 9V6a4 4 0 018 0v3" />
              </svg>
            </div>
            <h2 className="text-title font-semibold text-text-primary mb-2">Vault is locked</h2>
            <p className="text-sm text-text-secondary mb-4">Enter your vault password to unlock and access encrypted files</p>
            <Button onClick={() => setUnlockOpen(true)}>Unlock Vault</Button>
          </Card>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </div>
        )}

        {/* Unlock Modal */}
        <Modal open={unlockOpen} onClose={() => setUnlockOpen(false)} title="Unlock Vault">
          <div className="space-y-4">
            <Input
              label="Vault Password"
              type="password"
              placeholder="Enter vault password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleUnlock()}
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setUnlockOpen(false)}>Cancel</Button>
              <Button onClick={handleUnlock} disabled={unlocking || !password.trim()}>
                {unlocking ? "Unlocking..." : "Unlock"}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </AppShell>
  );
}
