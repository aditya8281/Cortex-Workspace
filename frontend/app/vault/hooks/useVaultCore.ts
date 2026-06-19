"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../src/shared/auth/AuthProvider";
import {
  apiVaultStatus,
  apiVaultLock,
  apiVaultUnlock,
  apiVaultListFiles,
} from "../../../src/shared/auth/cortexApi";
import type { VaultFileEntry, VaultStatus } from "../../../src/shared/types";

export default function useVaultCore() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [status, setStatus] = useState<VaultStatus | null>(null);
  const [files, setFiles] = useState<VaultFileEntry[]>([]);
  const [recursiveFiles, setRecursiveFiles] = useState<VaultFileEntry[]>([]);
  const [currentFolder, setCurrentFolder] = useState("/");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [vaultPassword, setVaultPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  async function refreshStatus() {
    try {
      const next = await apiVaultStatus();
      setStatus(next);
      if (!next.locked) {
        await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
      } else {
        setFiles([]);
        setRecursiveFiles([]);
      }
    } catch {
      setStatus({ locked: true, has_vault_password: false });
    }
  }

  useEffect(() => {
    if (!user) return;
    refreshStatus();
  }, [user]);

  async function loadFiles(folder = "/") {
    try {
      setFiles(await apiVaultListFiles(folder, false));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load vault files");
    }
  }

  async function loadRecursiveFiles() {
    try {
      setRecursiveFiles(await apiVaultListFiles("/", true));
    } catch { /* silent */ }
  }

  const handleUnlock = async () => {
    if (!vaultPassword.trim()) return;
    setLoading(true); setError(""); setSuccessMsg("");
    try {
      await apiVaultUnlock(vaultPassword);
      setVaultPassword("");
      await refreshStatus();
      setSuccessMsg("Vault unlocked.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid vault password");
    } finally { setLoading(false); }
  };

  const handleLock = async () => {
    setLoading(true); setError(""); setSuccessMsg("");
    try {
      await apiVaultLock();
      setStatus((prev) => ({ locked: true, has_vault_password: prev?.has_vault_password ?? false }));
      setFiles([]); setRecursiveFiles([]);
      setSuccessMsg("Vault locked.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to lock vault");
    } finally { setLoading(false); }
  };

  return {
    user,
    authLoading,
    status,
    files,
    recursiveFiles,
    currentFolder,
    loading,
    error,
    successMsg,
    vaultPassword,
    showPassword,
    setStatus,
    setFiles,
    setRecursiveFiles,
    setCurrentFolder,
    setLoading,
    setError,
    setSuccessMsg,
    setVaultPassword,
    setShowPassword,
    refreshStatus,
    loadFiles,
    loadRecursiveFiles,
    handleUnlock,
    handleLock,
  };
}
